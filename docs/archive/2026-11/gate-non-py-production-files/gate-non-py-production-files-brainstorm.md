# Brainstorm: gate-non-py-production-files

## Executive Summary
During Phase 5, a non-`.py` file that an impl-plan Task lists under **Production files** (e.g. `h-mad/scripts/hmad-dispatch.sh`) passes no TDD judge and no wire-pin check on any host; gate such files **by their Task, not by their suffix**, on all three write gates, and leave unlisted non-`.py` files allowed as today.

## Problem Statement
Row 2856 in `docs/skill-candidates.md` (skills defect #8), gate half. The report half landed in `af943118`: wire-pin 5b now prints `ungated: <path> — not .py, so no TDD judge or wire-pin covers it`. It reports the hole but does not close it. h-mad's largest production file, `h-mad/scripts/hmad-dispatch.sh` (258 KB), is a shell script, so the code most Phase-5 tasks in this repo touch is the code the TDD discipline does not reach.

Premise re-measured on `origin/main` `5cc9e270` (2026-11-03, this session). It still holds; the line numbers have moved since the row was filed at `190939a8`:

- **Parser.** `_PY_TOKEN_RE = re.compile(r"`([^`]+\.py)`")` (`h-mad/scripts/h_mad_wire_pin_gate.py:102`, used at `:247`) fills `task["production"]` with `.py` tokens only. Non-`.py` tokens go to `task["ungated"]` (`:249`). A probe Task listing `h-mad/bin/hmad-dispatch.sh` and `h-mad/scripts/a.py` parses to `production=['h-mad/scripts/a.py']`.
- **Judge.** `h_mad_tdd_judge.resolve` maps a target to its Task by realpath against `task["production"]` (`h_mad_tdd_judge.py:319`) and has no suffix rule of its own. It inherits the drop from the parser.
- **Claude gate** (`h-mad/hooks/h-mad-tdd-gate.sh`). The `ALL_SUFFIX_NAMES` block (around `:305`) allows `*.sh|*.bash|*.md|*.json|…` outright. The `ALL_NON_PY` block (`:318`) then allows anything that is not `.py`. The judge is never consulted for these files.
- **Codex gate** (`h-mad/hooks/h-mad-codex-tdd-gate.py:335`) and **agy gate** (`h-mad/hooks/h-mad-agy-tdd-gate.py:177`). Both judge a target only when `_is_production_python(relative)` (`h-mad/scripts/h_mad_target_identity.py:334`) is true. That function returns `False` for any non-`.py` suffix.
- **Other `_parse_tasks` consumers.** `h_mad_assemble_tdd.assemble` (`:508`), `h_mad_wire_pin_gate.check`/`main` (`:311`, `:540`) and `h_mad_wire_registry.challenge` (`:362`). They currently see `production` as `.py`-only.

## Proposed Approach
**Gate by Task membership, not by suffix.**

1. **Parser.** Record every backticked production path, not only `.py`. The open question below is whether that goes into `production` itself or into a sibling field.
2. **Judge.** Resolve a non-`.py` target to its Task exactly as for `.py`, by realpath against the Task's production list. Once resolved, apply the same RED/GREEN evidence rules. The Task's tests are still pytest files, which is how `.sh` code is tested here.
3. **Three write gates.** A non-`.py`, non-test target is judged **iff** the active feature's impl-plan lists it in some Task's Production files. Otherwise it is allowed, unchanged from today. This keeps the existing `.md`/`.json`/doc/fixture writes free during 5d/5e.
   - Claude: the `ALL_SUFFIX_NAMES` and `ALL_NON_PY` early-allows become "allow unless listed".
   - Codex and agy: `_is_production_python(relative) or listed_production(relative)`.
4. **Residual, stated exactly.** A non-`.py` production file that no Task lists stays ungated. That is the case wire-pin 5b already prints as `ungated:` if it is listed. An unlisted one is not reported at all; it is out of scope by operator decision (2026-11-03: allow unlisted).
5. **Verification.** Drive all three gates end to end with the `verify-hmad-gates` skill: a listed `.sh` is denied without RED and allowed with it, and an unlisted `.sh` is allowed.

## Alternatives Considered
- **Deny unlisted script suffixes** (`.sh`, `.bash`, `.js`…) unless a Task maps them. Rejected by operator (2026-11-03): it would block legitimate helper edits mid-run and make a forgotten mapping a halt.
- **Judge every non-test file.** Rejected by operator: 5d/5e routinely write `.md`/`.json`, and every such write would need a Task.
- **Parser + Claude hook only, with codex/agy filed as follow-ups.** Rejected by operator: codex is the default Phase-5 implementer, so the fix would miss the path that actually writes the code.
- **Widen `_PY_TOKEN_RE` to every path and stop there.** Rejected: the write gates filter by suffix independently of the parser, so a parser-only change closes nothing on any host. It also silently changes what wire-pin and the wire registry check.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| Changing `task["production"]` alters wire-pin / wire-registry / assemble_tdd behaviour. These consumers assume `.py` (symbols, imports). | H | Prefer a separate field (e.g. `production_any`) read only by the judge and the gates, or audit every consumer via `graft callers _parse_tasks --depth all` and pin each one's behaviour with a test before the change. |
| A gate change that is inert on one host and looks fixed everywhere (fail-open). | M | Mutation-test every new guard. Run verify-hmad-gates per host, with a control that runs the same `.sh` write unlisted. |
| The Claude hook is bash, and its early-allows are fast paths. Judging non-`.py` adds a python call per listed write. | L | Only listed targets pay. Unlisted targets keep the early allow. |
| Editing the live hooks breaks the in-flight lane in `~/orca/skills`, since h-mad is symlinked from there. | M | All work happens in this worktree (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files`). Merge to main only at Phase 7. |
| An alias spelling of a listed `.sh` (symlink, case fold, hardlink) escapes the listing match. | M | Reuse the realpath and kernel-canonical identity the `.py` path already uses (`h_mad_target_identity`). Do not add a second matcher. |
| The judge's RED discovery or test-path derivation assumes `.py` (`h_mad_derive_test_path.sh`). | M | Re-measure in Spec. For a non-`.py` target, use the Task's listed Test files. Do not derive a test path from the name. |

## Dependencies
- The impl-plan Task grammar (`_TASK_RE`, `_PATHS_FIELD_RE`) is unchanged.
- The `verify-hmad-gates` skill is used for end-to-end proof.
- No external systems.

## Open Questions
- Should the parser widen `production` itself, or add a sibling field so `.py`-specific consumers (wire-pin symbol checks, wire registry, assemble_tdd) are untouched? Settle it in Spec from the consumer census.
- Should wire-pin 5b's `ungated:` report change wording, or disappear, once listed non-`.py` files are judged? It currently says "no TDD judge … covers it", which becomes false.
- Does the judge derive any test path from the production file name (`h_mad_derive_test_path.sh`), and if so, what does a `.sh` derive to?
- Which judge verbs other than `resolve` filter by suffix (`implementer`, mutation-spec lookup)?

## Version History
- v1.0: Initial brainstorm draft (2026-11-03). Operator scope answers: allow unlisted, all three gates, separate worktree off `origin/main`.
