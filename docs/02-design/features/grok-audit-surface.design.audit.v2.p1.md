AUDIT-grok-audit-surface-design-v2-BEGIN
## Summary

The design has unresolved extraction, leak-control, provenance, and test-discrimination gaps. The table reconciles every acceptance criterion; “implemented-as-written” describes planned coverage, not verified implementation.

Evidence: 14 files opened, 6 greps run.

| Acceptance criterion | Classification | Design coverage or gap |
|---|---|---|
| AC-1.1 | restated | D11 excludes truncated effort but does not require `format=grok`. |
| AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8 | implemented-as-written | D8, D11, D14–D15, runtime-reference deliverable. |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5 | implemented-as-written | D4–D6, ledger schema and seed construction. |
| AC-2.6 | restated | Root validation happens at construction, although S1 reuses the mutated root. |
| AC-2.7 | restated | D3 permanently exempts metadata filenames without the complete content-sensitive catch-all. |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6 | implemented-as-written | D3, D8–D10, D12, D15. |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4 | implemented-as-written | D12–D13; the count assertion is specified, although the extraction algorithm has a separate defect below. |
| AC-4.5 | restated | D12 permits dropping all should-fix findings from a report. |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5 | implemented-as-written | D1–D2, D4–D13, refusal and verdict fixtures. |
| AC-6.1, AC-6.2, AC-6.2a, AC-6.3, AC-6.4 | implemented-as-written | D9, D14–D15, outcome-specific doc pins. |
| AC-7.1, AC-7.2, AC-7.3, AC-7.4 | implemented-as-written | D14 and wrapper/doc pins. |
| AC-8.1, AC-8.2 | implemented-as-written | Three-pass union and evidence-floor pins. |
| AC-8.3 | absent | A falsification test name does not specify the required rejected-finding ledger instruction. |
| AC-9.1, AC-9.2, AC-9.3, AC-9.4, AC-9.5 | implemented-as-written | Gate pins, G2–G5, D14. |
| AC-10.1, AC-10.2, AC-10.3 | implemented-as-written | Wrapper pins, W1–W6 and G1. |

## Must-fix

- AC-1.1 is restated as “not truncated,” which is narrower than requiring a positively identified grok effort shape. D11 only requires an effort item to exist and tests its truncated prefix; a recognized `codex-text` or unreadable-effort item beside otherwise passing observations has no specified rejection. Require `format=grok`, with an explicit closed-vocabulary refusal for other shapes, or reconcile the weaker requirement into the spec before implementation.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``and the cycle's `Effort:` block reports `format=grok` (shape `grok`), not `grok-truncated`.``
  quote: docs/02-design/features/grok-audit-surface.design.md › ``The grok `Effort:` item for `p1`, when the grok cycle reached dispatch: absent → `input_unparseable:<grok/auditcycle.txt>` (the wrapper renders one for every pass that carried a log).``

- AC-2.6's “before any dispatch” validation is narrowed to one root-construction check during S1. The shared root then accumulates collected reports and retained logs before agy and codex run; those files can contain original spans or expected findings. Record each cycle, remove its by-products, and rerun the content and git-reach checks before the next dispatch in that same root.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``Before any dispatch, the probe reads every regular file in the root``
  quote: docs/02-design/features/grok-audit-surface.design.md › ``For S1 the three cycles share the one root, so the `build-root` line runs once and its `.root.txt` file is passed to all three `record-cycle` calls.``

- AC-2.7's content-sensitive calibration-data catch-all is restated as an unconditional six-filename exclusion. The proposed replacement scans only seeded and expected spans, so an excluded metadata file carrying an actual finding's text, but neither span, remains exempt from the whole-file equality check. Make those exclusions conditional on the full spec predicate and add an opposed fixture using a non-seed finding, or obtain a spec change explicitly permitting the narrower set.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``Any other file that carries a seed's `seeded` span or `expected` sentence, or the text of a finding filed on a seeded document, also counts as calibration data and follows the same rule.``
  quote: docs/02-design/features/grok-audit-surface.design.md › ``The catch-all still reaches the six: triggers (ii) and (iii) scan every `main` blob for every seed's `expected` and `seeded` text whatever the file.``

- AC-4.5 is restated to permit unpublished should-fix hits. “Never enter the bar” does not authorize discarding observational findings; the design explicitly drops them on a walk mismatch, and the extraction defect below makes that reachable. Preserve and publish them through a gate-equivalent walk, or put this exception into the spec before accepting it.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``Should-fix hits are published separately and never enter the bar.``
  quote: docs/02-design/features/grok-audit-surface.design.md › ``its should findings are not written, and `extract` prints `SHOULD-SKIPPED: <report> walk=<n> gate=<m>`. Residual: a should hit in such a report is not published.``

- AC-8.3's rejected-finding ledger instruction is absent. The PASS-only test list names grok falsification, but neither its assertion nor D14 specifies the required rejection-ledger cross-reference. Add both required instructions to the PASS text and pin both in the doc test.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``and that a rejected one is recorded per §"Record a rejected finding in the rejections ledger, never in a gated document".``
  quote: docs/02-design/features/grok-audit-surface.design.md › ``test_never_gate_section_names_grok_falsification``

- D12's extraction algorithm disagrees with the shipped gate on valid nested bullet groups. For a parent `Build defects:` and two nested findings, counting real-parent groups yields one finding while `classify` yields three; a real parent with a `None` child followed by a real child yields one versus two. The gate conditionally uses `_collapses` and `_flat_findings`, which the proposed walk omits; implement that decision structure and add direct parity fixtures instead of relying only on a patched classifier. Otherwise ordinary reports make must extraction UNREADABLE and should extraction lose findings.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ``Each group with a real parent payload is one finding, whose text is the group's lines joined.``
  Reproduction (prints design-walk count then gate count): `python3 -B -c 'import sys; sys.dont_write_bytecode=True; sys.path.insert(0,"h-mad/scripts"); import h_mad_audit_gate as g; b="- Build defects:\n  - A\n  - B"; print(len([x for x in g._bullet_groups(b.splitlines()) if x["parent"] is not None]), g.classify("## Must-fix\n"+b+"\n## Should-fix\nNone\n")["must_count"])'` → `1 3`.

- Calling the agy model helper immediately after the cycle does not attribute its answer to that dispatch. `agy_from_cli_logs` sorts all logs by modification time and compares only its newest two; a controlled pair with an unchanged dispatch log reports `dispatch-model` alone, but reports `peer-model` when two more recently modified peer logs both carry that model. Establish dispatch-specific log provenance, or publish UNKNOWN when attribution is unavailable; timing alone violates the assumption-verification requirement.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ``running it right after the agy cycle is what makes that process this dispatch``
  Evidence: h-mad/scripts/h_mad_resolved_model.py:123–149; the controlled pair patched only the helper's log enumeration, contents and mtimes, leaving the dispatch log unchanged.

- The promised discrimination coverage omits tests over unchanged behavior. No W/G/C/K row targets `test_union_three_passes_all_clean_pass` or `test_codex_agy_cycle_stamps_carry_the_legs_that_ran`; P-rows explicitly cover Probe and Smoke fixtures only. Add targeted mutants that make those assertions fail, including an always-failing union and removed/forced two-surface stamp wiring, before claiming those tests are enforced.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ``**Tests over unchanged code** (FR-8, FR-9, FR-10, AC-7.2's stamp pin, the kept doc pins) are shown able to fail only by their mutation rows.``

- The load-bearing three-surface stamping premise lacks its runnable measurement command. The readings describe a deleted scratch pytest and its output, but neither the readings' command block nor the test design supplies the scratch invocation and setup that produced the exact two-stamp envelope. Preserve an inline throwaway script or exact runnable command beside that output; “scratch pytest, deleted” does not meet the base requirement that behavioral premises carry their command.
  class: measurement
  quote: docs/02-design/features/grok-audit-surface.design.md › ``2 stamps (`p1`, `p2`), each `"legs": ["agy", "codex", "grok"]`; about 20 s wall (scratch pytest, deleted after the run)``

## Should-fix

- Make the synthetic-source override available and unambiguous on every mode that validates a ledger. D1 says invented fixtures pass `--sources`, but D2 lists it only for `check-ledger`; `build-root`, `extract`, `score` and `rescore` also need the same source mapping. Specify either a shared global option or the option on each relevant subcommand and its in-process calls.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ``overrides the constant, and only the synthetic fixtures pass it.``

- Create the run directories before opening their output files. The first `versions.txt` redirection needs `data/s1`, and `tee` needs the parent `stem` directory; the only displayed `mkdir -p` occurs after `build-root | tee`. Include explicit initial setup so the filled runbook works from an empty kept directory.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ``ROOT=<path from ROOT: READY>; STEM="$KEEP/run-<cal12>/stem/<cycle-id>"; mkdir -p "$STEM"``

- Refresh the design's comparisons against the paired plan. The current plan already corrects R13 and specifies fresh dispatch roots, so the claims that it says the interpreter is absent and still has the old S0b root count describe an earlier plan revision. This does not change the chosen implementation, but obscures which disagreements remain.
  class: measurement
  quote: docs/02-design/features/grok-audit-surface.design.md › ``This **contradicts the brief and plan R13**``
  quote: docs/01-plan/features/grok-audit-surface.plan.md › ``which has pytest; v1.3's "absent" was a PATH condition of that shell, not a property of the machine.``

## Nit

None

🌱 graft saved ~113,532 tokens this turn, 3 calls.
AUDIT-grok-audit-surface-design-v2-END
