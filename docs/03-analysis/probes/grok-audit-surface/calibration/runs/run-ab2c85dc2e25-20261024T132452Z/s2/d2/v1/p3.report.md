## Summary
The design covers the collector, the CLI, the transport refusal, the verb, and the recipe, and most acceptance criteria match the spec. The gate sketch returns 1 where AC-3.1, AC-2.9, and `gate()` require 2; the CLI is specified to emit both one and two `[H-MAD]` markers; AC-2.11 is narrowed so an empty identical pair is `MISSING`; and the codex recipe pins a stable basename that step 6.6 no longer stages and that `h_mad_assemble_audit.py` will not hand twice.

| AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.6a | implemented-as-written |
| AC-2.6b | implemented-as-written |
| AC-2.7 | implemented-as-written |
| AC-2.8 | implemented-as-written |
| AC-2.9 | restated |
| AC-2.10 | implemented-as-written |
| AC-2.11 | restated |
| AC-2.12 | implemented-as-written |
| AC-3.1 | restated |
| AC-3.2 | implemented-as-written |
| AC-3.3 | restated |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.5a | restated |
| AC-3.6 | implemented-as-written |
| AC-3.7 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |

Evidence: 9 files opened, 24 greps run.

## Must-fix
- AC-3.1 is restated: D3's refusal sketch returns 1, while the spec and the next paragraph of the same section require exit 2. Copying the sketch fails a test that asserts exit 2, and exit 1 is the traceback exit D1 distinguishes from the operational exit 2.
  class: build
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `return 1`
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `and exits 2; `gate()` accepts rc ∈ {0, 2}`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `exit 2. The same for the hand-staged`
- AC-2.9 step (i) is the same sketch: the incident replay requires `h_mad_audit_gate.py <RP>` to exit 2, but the only refusal body in the design returns 1, so the suite half cannot pass as specified.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `exit 2 (cannot gate`
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `return 1`
- AC-3.3 is restated: the design says `gate()` returns `("INVALID", 0, 0, [])` because rc 2 is accepted, but the sketch's rc 1 is outside that set. Verified in `h_mad_audit_cycle.gate`: a return code other than 0 or 2 raises `OperationalError` before the INVALID early return, so `combine()` never sees `no_gate_sections`.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `rc 2 is already mapped`
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `and exits 2; `gate()` accepts rc ∈ {0, 2}`
  quote: h-mad/scripts/h_mad_audit_cycle.py › `if result.returncode not in (0, 2):`
- AC-2.11 is restated, narrower than the spec. The spec says an existing byte-identical docs file with no `<RP>.done` is `COLLECT: OK`. The design requires non-empty bytes and ends an empty identical pair as `MISSING`, and it pins that narrower verdict with a test the spec does not have.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `AC-2.11: Existing-identical docs file with `--surface` given and `<RP>.done` absent →`
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `short-circuit requires non-empty bytes — so it also ends MISSING`
- The CLI marker contract is two different counts. D2 says every exit path carries exactly one `[H-MAD]` marker, which matches FR-2 (one `COLLECT:` line followed by one marker). Error Handling says every CLI exit path carries exactly two. A test that counts marker lines cannot satisfy both, and v1.2 already recorded the contract as one marker.
  class: build
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `so every exit path carries exactly one `[H-MAD]` marker.`
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `carries exactly two `[H-MAD] … collect`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `followed by `[H-MAD] <feature> collect <verdict>``
- AC-3.5a is restated, and the D5 recipe cannot be re-run. The design tells the test to read a 6.6 literal `RP=/tmp/audit_<feature>_<phase>_cycle<N>.report.md` out of SKILL.md; the file's 6.6 literal is `RP=/tmp/audit_<feature>_<phase>_cycle<N>_run$RUN.report.md`. The recipe then reuses a stable `…_codex.report.md` and only `rm -f`s `$RP` and `$RP.done`. `h_mad_assemble_audit.py` halts when that `--out` still exists or when the path was already claimed under `~/.cache/h-mad/handed` (`ASSEMBLE: HALT … report_path_handed`), and the recipe does not mint a new `RUN` or clear either hold.
  class: build
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `RP=/tmp/audit_<feature>_<phase>_cycle<N>.report.md`
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `RP=/tmp/audit_<feature>_<phase>_cycle<N>_codex.report.md; rm -f "$RP" "$RP.done"`
  quote: h-mad/SKILL.md › `RP=/tmp/audit_<feature>_<phase>_cycle<N>_run$RUN.report.md`
  quote: h-mad/scripts/h_mad_assemble_audit.py › `was handed to an earlier leg`

## Should-fix
- D1's `_collected_path` body indexes `audit_dirs`, which is not defined in `h_mad_audit_cycle.py`. The live map is `_AUDIT_DIRS`. Pasting the sketch raises `NameError` before any path is built.
  class: build
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `return project_root / audit_dirs[phase] / f"{feature}.{phase}.audit.v{cycle}.{token}.md"`
  quote: h-mad/scripts/h_mad_audit_cycle.py › `_AUDIT_DIRS = {`
- The D1 blocks are complete function bodies, and the "observed today" return set is only `report-file`, `out`, and `none`. Live `collect()` also returns `unscorable:<reason>`, threads `PassSpec.log_path`, and skips `report_wait` when `grace` is 0. Replacing the functions with the sketches deletes that screen.
  class: build
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `delivered ∈ {"report-file","out","none"}`
  quote: h-mad/scripts/h_mad_audit_cycle.py › `UNSCORABLE_PREFIX = "unscorable:"`
- Two placement claims are stale and contradict D5. The new section is a new top-level heading after `## Putting \`hmad-dispatch\` on PATH`, but Invariant Compliance says the SKILL.md edit is additive inside an existing section, and the insertion cite `SKILL.md:1791` is not that heading (it is at line 2962). The heading order the docs test pins is unchanged, so the line number and the compliance sentence do not move the edit.
  class: measurement
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `SKILL.md edit`
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `is additive inside an existing section.`
  quote: docs/02-design/features/audit-report-docs-copy.design.md › `(SKILL.md:1791)`

## Nit
- `PassSpec.out_path` is described as sitting second. The tuple is `index report_path out_path rc log_path`, so `out_path` is third. The keyword constructor in D2 still builds a valid spec because `log_path` defaults to `None`.
- The recipe's gate invocation is the placeholder `<the path= the COLLECT: OK line printed>`, which is not a command an operator can run until it is replaced with the `path=` field from the `COLLECT: OK` line.
