Counts: `test_h_mad_collect_report.py` 28 passed/0 failed; `test_h_mad_audit_gate.py` 70 passed/0 failed; `test_h_mad_audit_cycle.py` 79 passed/0 failed; `test_hmad_dispatch_collect_report.py` 4 passed/0 failed.
Cross-check: static `def test_` counts were 26/52/67/4; pytest collected 28/70/79/4 due parametrization, matching executed counts.

Anti-gaming: all 181 collected items are discriminating. Real-tree checks are non-vacuous: `docs/**/*.audit.v*.md` found 374 files; p-artifact globs found 32 live plan, 28 live design, 119 archive, and the real-artifact parity parametrization collected 8 cases. The mutation spec has 23 named mutations; I did not execute the harness.

P1 confirmed: `h_mad_audit_cycle.py:96` `"plan": Path("docs/01-plan/features"),`; `:97` `"design": Path("docs/02-design/features"),`; `:104` `/ f"{feature}.{phase}.audit.v{cycle}.{suffix}.md"`.
P2 confirmed: `h_mad_audit_cycle.py:63` `if not SURFACE_RE.match(surface) or PASS_INDEX_RE.match(surface):`; `:64` `raise ValueError(f"invalid surface token: {surface!r}")`.
P3 confirmed/scoping accurate: write-path AST builders exactly `['h_mad_audit_cycle.py:_collected_path']`; reader rebuilds exist in `h_mad_cycle_counts.py` and `h_mad_do_preconditions.py`. Source line: `h_mad_audit_cycle.py:104` `/ f"{feature}.{phase}.audit.v{cycle}.{suffix}.md"`.
P4 confirmed: `h_mad_audit_cycle.py:146` `raise CollectConflict(collected_path, "report-file")`; `:236` `raise CollectConflict(collected_path, "out")`; shared readback `:130` `if not _readback_equal(collected_path, data):`.
P5 confirmed: `h_mad_audit_cycle.py:285` `if spec.report_path == collected_path:`; `:287` `if not marker.exists():`; `:289` `marker.unlink(missing_ok=True)`.
P6 confirmed: `h_mad_audit_gate.py:279` `if is_transport_path(args.audit_file):`; normal scoring follows at `:307` `result = classify(text, acknowledged)`.
P7 confirmed: `h_mad_audit_gate.py:19` `TRANSPORT_RE = re.compile(r"^audit_[^.]+\.report\.md$")`; docs grammar source is P1 `:104`. This is a property test, not a production assert; sound because it guards the independent grammars without adding dead runtime assertions.
P8 confirmed: `h_mad_collect_report.py:21` phase choices; `:25` required project root flag; `:36-37` single usage marker plus rc2; `:44-45` operational marker plus rc2.
P9 confirmed: `hmad-dispatch.sh:3525` `collect-report) _cmd_collect_report "$@" ;;`; `:1429` `python3 "$here/h_mad_collect_report.py" "$@"`; unknown fallback `:3538` returns 2.

Wire mutations: removing only the `collect-report)` connection made WIRE-PIN fail: 1 failed, rc 2 unknown verb instead of stub rc 7; restored, WIRE-PIN 1 passed. Changing unknown fallback to unconditionally `_cmd_collect_report "$@"` made unknown-verb guard fail: 1 failed, stub rc 7 instead of rc 2; restored, dispatch collect-report file 4 passed. Final `git status --short` clean; tree restored to committed state.

STATUS: DONE