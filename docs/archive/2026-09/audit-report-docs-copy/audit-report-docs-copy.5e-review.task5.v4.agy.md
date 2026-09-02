I have reviewed the changes in `h-mad/SKILL.md` against the requirements and the actual behaviour of the helper scripts. 

Here are the verification results:

1. **Cycle 3 Findings**: Both findings are genuinely closed.
   - The whitespace truncation defect is fixed. The `sed -n 's/^COLLECT: OK path=\(.*\) delivered=.*/\1/p'` command uses a greedy `\(.*\)` match which correctly captures the entire path up to the final ` delivered=` delimiter, preserving spaces perfectly.
   - The interactive shell termination defect is fixed. The `exit 1` has been removed in favor of a standard `if/else` block that gracefully prints the halt marker on failure and runs the gate on success.
2. **Output Shape Extraction**: The sed extraction precisely matches `h_mad_collect_report.py`'s actual output format (`COLLECT: {verdict} path={printed_path} delivered={delivered}[ forced=1]`). The trailing `.*` correctly absorbs the optional ` forced=1` flag without affecting the path capture group.
3. **Contextual Claims**: The changes strengthen the workflow without weakening any surrounding claims. The instruction to "gate the printed docs path, never `$RP`" is perfectly honored by piping the extracted `$DOCS` directly into `h_mad_audit_gate.py`.
4. **Factual Accuracy**: 
   - The `h_mad_collect_report.py` registry entry is completely accurate. Tracing through `_collect_unguarded` into `_copy_collected_report` and `_finalize_write` confirms it does indeed perform strict readback and throws an `OperationalError` (exit code 2) on failure.
   - The `orchestration-mode.md` row accurately describes the `collect-report` verb. 
5. **Scope boundaries**: No out-of-scope modifications were made. The file diff perfectly matches the requested additions.

VERDICT: COMPLIANT
