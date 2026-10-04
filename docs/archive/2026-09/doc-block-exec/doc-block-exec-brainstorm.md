# Brainstorm: doc-block-exec

## Executive Summary

Ship `h-mad/scripts/h_mad_doc_block_exec.py` — extract a doc's fenced bash block by
heading plus an **explicit info-string tag**, substitute `<placeholders>` from a map, run it
under a per-block-declared shell in a `mktemp -d` cwd, and return rc + stdout + stderr — so that
the paste-along recipes in these skills are executed as tests rather than only read.

## Problem Statement

Four defects in the `audit-report-docs-copy` Task-5 recipe — a phase-hardcoded path, an
unimplemented halt, whitespace truncation, and a shell-killing `exit` — were invisible to prose
review and to a green suite, and became visible only when the fenced block was **extracted and
run against fixtures**. The extract+substitute+run harness that did it was hand-written inline in
`h-mad/tests/test_h_mad_collect_report_docs.py:309` (`run_recipe`), so the next doc recipe that
wants the same treatment re-writes it. Recurrence 4 on `docs/skill-candidates.md:1281`.

## Proposed Approach

A stdlib-only helper in `h-mad/scripts/`, shaped like every other entry in the Helper-scripts
registry: importable functions plus a CLI printing a `DOCBLOCK:` verdict token, exit 0 on a
verdict and 2 on a cannot-judge.

**Opt-in is an info-string tag on the fence** — ` ```bash hmad:exec `. The marker travels with
the block, so it cannot drift from what it marks; it is visible in the raw markdown; one grep
enumerates every executable block in the tree; and every renderer still highlights it as bash.
A block without the tag is never executed, which is what keeps this from becoming the blanket
sweep of all **68** bash fences the row forbids.

**Shell mode is declared per block, defaulting to strict.** `bash -euo pipefail` is the default
the row specifies. A block may declare `shell=plain` to run as an operator's paste actually runs,
because the four measured defects live in *that* environment: a shell-killing `exit` is only a
defect because the operator pastes into an interactive shell, and under `-e` an unrelated non-zero
masks it. Defaulting to strict keeps the row's constraint; allowing `plain` keeps the defect class
that motivated the row findable. The existing inline harness uses plain `bash -c` today.

**Placeholder substitution is an explicit map**, never inference. The inline harness rewrites
`~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py` to point at the tree under test; that is a
substitution the *caller* knows about and the doc does not.

**Every run is in a fresh `mktemp -d`**, removed afterwards, so a recipe that writes files cannot
touch the repo or leak between tests.

## Alternatives Considered

- **HTML comment marker above the fence** (`<!-- hmad:exec name=… -->`): allows named addressing
  and richer metadata, and keeps the info string clean. Rejected as the default because it is a
  second line that can drift from its fence when either moves, and the naming benefit is
  recoverable later by adding a `name=` key to the info string itself.
- **No in-doc marker; caller addresses by (heading, index)**: zero doc churn. Rejected — the doc
  then carries no record that a block is under test, and reordering blocks under a heading
  silently re-points the index at a different block, which is a false pass with no error.
- **Test-only helper module under `h-mad/tests/`**: smaller surface. Rejected — it cannot be run
  by hand to debug a failing recipe, and test-only modules in this repo carry no mutation spec,
  so the helper that exists to catch silent doc defects would itself be unguarded.
- **Always `bash -euo pipefail`** (the row as literally written): rejected per the shell-mode
  reasoning above — it cannot reproduce the environment the motivating defects were found in.
- **Always plain `bash -c`** (what the inline harness does): rejected — loses strict mode's
  ability to surface unset variables and swallowed pipeline failures.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| **Adding ` hmad:exec` to a fence breaks two existing extractors.** `test_h_mad_collect_report_docs.py:270` and `:412` both use `re.findall(r"```bash\n(.*?)```", …)`, which requires `\n` immediately after ` ```bash `. A tagged fence matches zero blocks. | **H** — certain, if any tagged fence lands in a section those extractors read | Fails LOUD, not silent: `_gate_bash_block()` asserts `blocks` is non-empty. Migrate both call sites to the new helper in the same task that tags the first fence; pin the migration with a test. |
| A tagged block is executed with side effects on the repo | M | Every run in `mktemp -d`; the helper never runs with the repo as cwd. Pin with a test asserting cwd is not the repo root. |
| The helper becomes a blanket sweep by a later "convenience" flag | M | No API that takes a directory or a glob. Address is always (doc, heading, tag); a `--all` flag is out of scope and named so in the spec. |
| `shell=plain` is chosen by default-by-habit, losing strict mode | M | Default is strict; `plain` must be written explicitly on the fence, so it is visible in review. |
| Substitution silently no-ops when its anchor drifts — the `.replace()`-matched-nothing failure this repo has shipped before | **H** | Refuse a substitution whose key is absent from the block; that refusal is a verdict (`DOCBLOCK: SUBST_MISSING`), not a silent pass. This is the single most load-bearing guard in the feature. |
| Timeouts: a recipe that blocks hangs the suite | M | Bound every run; never `timeout`/`gtimeout` (forbidden — §"What you NEVER do"), use the same process-group watchdog `hmad-dispatch run` uses, or `subprocess.run(timeout=…)` since this is Python. |
| The 68-fence figure is stale | L | **Re-measured this session: 68 across 10 files under `h-mad/` + `handoff/`, excluding archive** (control: 83 opening fences of all languages). The carried premise holds. |

## Dependencies

None. Stdlib-only, consistent with every other helper in `h-mad/scripts/`. It reads markdown files
and runs `bash`, both already assumed everywhere in this skill.

## Open Questions

- Should the info string carry a `name=` key now, or is (heading, tag, ordinal) enough addressing
  for the first consumer? Leaning ordinal-only; `name=` is additive later and un-needed at N=1.
- Does the CLI need a `--list` mode enumerating tagged blocks in a doc? Cheap, and it is the
  answer to "is this block under test?" — but it is not needed by the migration, so it belongs in
  the spec's out-of-scope list unless it earns its way in.
- Which fences get tagged in this feature? Proposal: **only** the Second-surface gate block that
  the existing `run_recipe` already executes. Tagging more is a separate, later decision — the
  point of the opt-in marker is that tagging is deliberate.

## Version History

- v1.0: Initial brainstorm draft.
