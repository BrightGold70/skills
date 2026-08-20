## Summary
The design for the `audit-cycle` verb successfully composes the existing h-mad tools into a robust two-pass union gate, implementing all 52 ACs from the specification as written. However, the design contains two critical Axis B invariant violations: it independently re-implements the gate's finding-extraction logic without a differential test (risking silent divergence on prose findings), and it fails to verify its file-write mutations when saving collected reports.

| Spec Identifier | Classification |
|---|---|
| AC-1.1 through AC-10.5b | `implemented-as-written` |

## Must-fix
- **Axis B - Single-source contract**: The helper extracts citations for the premise checklist by independently re-implementing the section-parsing logic using imported primitives (`_BULLET_MARKERS`), rather than calling a single authoritative extraction function. Because `h_mad_audit_gate.py`'s `_count_section_findings` falls back to counting a prose block as a finding when no bullets are present, but the helper's `premise_items` looks only for bullets, a prose finding will cause `GATE: FAIL must=1` while the checklist extracts 0 items, silently diverging. The design must either extract findings via a single shared authoritative function (e.g., refactoring the gate to expose it) OR add a differential test asserting that `len(extracted_bullets) == gate_must_count` across all passes.
- **Axis B - Mutation verification**: The design specifies writing the collected report to `<audit-dir>/<feature>.<phase>.audit.v<N>.p<i>.md` during the `collect` ladder (either by copying from `report-file` or writing the stdout from `extract_report`), but does not verify these file writes by re-reading the resulting state. Python file writes are mutations and must be explicitly verified (e.g., `assert collected_path.exists() and collected_path.stat().st_size > 0`) before proceeding, as an exit code or lack of exception is not sufficient evidence under the invariant.

## Should-fix
- **Incomplete CLI forwarding in no-pass mode**: In the "Architecture Overview" diagram, the `no-pass form` invocation example omits the `--project-root` flag, but the text below states `--project-root` is needed to derive the audit directory mapping. If `--project-root` is a required `argparse` argument, the shell will crash if it omits it. Ensure the shell forwards `--project-root` unconditionally even in no-pass mode, or explicitly configure `argparse` to make it optional.

## Nit
- **Subprocess exit 2 handling**: The text states `GATE: INVALID must=0 should=0` uses exit 2. While correctly handled as a verdict rather than an operational error, it's worth noting in the implementation plan that `subprocess.run` must use `check=False` (or catch `CalledProcessError`) to explicitly read this non-zero exit code without crashing the helper.
