AUDIT-gate-non-py-production-files-design-v2-BEGIN
## Summary
The design explicitly addresses all 56 acceptance criteria in their current spec form, including the corrected authorship arrangement and mixed-plan fail-closed behavior. Remaining issues concern Claude's target transport and the verification contracts; this was a static review, with no runtime probes or repository changes.

Evidence: 20 files opened, 14 greps run.

| Acceptance criteria | Axis C classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6, AC-5.7, AC-5.8 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5 | implemented-as-written |
| AC-7.1, AC-7.2, AC-7.3, AC-7.4 | implemented-as-written |
| AC-8.1, AC-8.2, AC-8.3, AC-8.4, AC-8.5 | implemented-as-written |
| AC-9.1, AC-9.2, AC-9.3, AC-9.4, AC-9.5 | implemented-as-written |
| AC-10.1, AC-10.2, AC-10.3 | implemented-as-written |
| AC-11.1, AC-11.2, AC-11.3, AC-11.4, AC-11.5, AC-11.6 | implemented-as-written |

## Must-fix
- **Preserve trailing newlines when decoding the selected target.** Bash command substitution strips trailing newlines, so the proposed decode can change a valid canonical name before the membership check and refuse it as `judge-error`. A representable counterexample is a plan listing `scripts/alias.sh`, a symlink to a code-like filename ending in a newline: the realpath matcher can list it, but Claude then loses that final byte. Use the existing `_pct_capture` mechanism and add a real-entry regression case with a failing Task test; codex and agy should agree with Claude. This is a transport defect inferred from the specified code, not an executed hook repro.
  class: build
  quote: docs/02-design/features/gate-non-py-production-files.design.md › ``LISTED_TARGET=$(_pct_decode …)``
  quote: h-mad/hooks/h-mad-tdd-gate.sh › `_pct_v=$(_pct_decode "$2"; printf '\001')`
- **The advertised case-sensitive-volume skip is an assertion failure.** The existing helper uses `assert os.path.exists(directory / "A")`; it never skips. Moreover, `test_case_insensitive_precondition_is_asserted` explicitly pins its AssertionError contract. Calling it as prescribed therefore does not implement the Test Boundaries exclusion. Specify an explicit skip precheck for the new volume-dependent cases, while preserving the existing helper contract, or correct the supported-volume policy and expected outcomes. The current premise cannot support the claimed verification behavior.
  class: build
  quote: docs/02-design/features/gate-non-py-production-files.design.md › ``- **Case folding.** The case-insensitive-volume cases (AC-3.3, AC-11.2) call `tdd_gate_support.assert_case_insensitive` first, which skips on a case-sensitive volume.``
  quote: h-mad/tests/tdd_gate_support.py › `assert os.path.exists(directory / "A"), "case-insensitive filesystem precondition failed"`
- **FR-1's Test Boundaries row exposes only a private helper.** The row assigns AC-1.1 through AC-1.5 exclusively to `_parse_tasks`, rather than a public parser or consumer interface, contrary to the audit's explicit Test Boundaries rule 3. Keep the spec-required parser unit tests as supplementary checks, but provide a public interface and corresponding contract coverage, or equivalent consumer-level integration coverage that exercises the real parser.
  class: build
  quote: docs/02-design/features/gate-non-py-production-files.design.md › ``| `h_mad_wire_pin_gate._parse_tasks` | AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5 | spec FR-1 AC inputs and expected lists; the six named `test_h_mad_parse_tasks_paths.py` tests unmodified | none | gate verdicts (host rows) |``
- **AC-10.1 is assigned non-test verification despite having a deterministic executable assertion.** The row declares `verified by: doc-review`, and the documentation tier explicitly leaves the phrase sweep as a manually recorded command. Absence of the forbidden phrases can and should be asserted by an integration test over the actual prose corpus; the existing token-presence tests do not enforce that absence. Add that automated assertion and establish its RED against the pre-change corpus. The current row violates Test Boundaries rule 4.
  class: build
  quote: docs/02-design/features/gate-non-py-production-files.design.md › ``| verified by: doc-review | AC-10.1 | the eight-branch `git grep` command in §Test Plan printing no line; pre-change hits in §FR-10 | none | wrapped phrasings (stated residual) |``

## Should-fix
None

## Nit
None

🌱 graft saved ~60,531 tokens this turn, 4 calls.
AUDIT-gate-non-py-production-files-design-v2-END

