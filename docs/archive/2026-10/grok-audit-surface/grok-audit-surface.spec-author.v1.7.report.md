SPEC-AUTHOR: DONE version=v1.7 path=/Users/kimhawk/orca/skills/docs/01-plan/features/grok-audit-surface.spec.md lines=291 sha256=5b4f6c39bf432645776318100da35484923474a26afebfae16925dc8459d7147

premises verified:
- Ownership before the write: mtime 1792365165, newest `- v1.6`, `git status --short` clean. Both were unchanged between my read and my first edit.
- Decision file `docs/03-analysis/grok-audit-surface.decision-2026-10-19-d4.md`: I copied the canonical sentence verbatim from its blockquote.
- grok on PATH, measured with the decision file's own re-derive command (`which -a grok | sort -u | ... --version`) on 2026-10-19 at HEAD abe47752. `/opt/homebrew/bin/grok` prints 1.0.1. `~/.grok/bin/grok` and `~/.local/bin/grok` both print `grok 1.0.62 (1474f9cbdd91) [stable]`. `head -1 ~/.grok/CHANGELOG.md` prints `# 1.0.52 — 2026-10-11`. See the contradiction below.
- Design last resort (design §D1 "The last resort", located by grep for `internal:<ExceptionName>`). score/rescore print `SEEDSCORE: UNREADABLE reason=internal:<ExceptionName>`. smoke maps to `SMOKE: UNREADABLE reason=input_unparseable:<path>`, not to `internal`. So the AC-5.1 sentence says "every other mode except the smoke".
- Design drift check (grep `not_descendant`). The design-author's DECISION already makes the score sha descend from the smoke commit, refused as `calibration_drift:not_descendant`, with test `test_drift_score_not_descendant_of_smoke_commit`.
- AC-5.4 count. A python slice from `  - AC-5.4:` to `  - AC-5.5:` gives 14 bullets and 15 forms, with calibration_drift counted as 2. "fifteen" is true and unchanged, because I added no form.

findings applied:
1. D4 version-agnostic. D4 now carries the canonical sentence verbatim, plus a pointer to the decision record. I removed every literal target version from:
   - the Premises version line (line 23 content, "grok --version on this machine prints …")
   - the FR-1 heading and description (the smoke now also records the binary path and the `--version` line)
   - AC-1.5
   - both AC-1.8 bullets
   - the Assumptions line
   AC-1.5 and AC-1.8 name `<version>` = the version the smoke recorded. The 1.0.41 sentence rule is unchanged.
2. AC-5.1: the scoped `internal` sentence (design-author v1.1 owed).
3. AC-2.7 and AC-5.4: the score sha must descend from the smoke commit. The failure is `calibration_drift:not_descendant`. There is no new form, and the count is still fifteen.

values swept:
- `grep -n '1\.0\.62' <spec>` returns 0 lines, both in the body and in Version History. No existing VH line held the value, and the new v1.7 VH entry deliberately does not spell it.
- `grep -c '1\.0\.52'` returns 0. `grep -n '1\.0\.41'` gives lines 23, 54, 80, 269, all unchanged sentences.
- `grep -n -i 'fifteen'` gives line 177 (AC-5.4 head), line 193 (the counting sentence) and VH line 290. All still say 15, re-derived as above.
- `grep -n 'not_descendant'` gives AC-2.7 (amended), AC-5.4 (amended) and history lines.
- There are no derived figures off a version.

contradictions found:
- The decision file's premise does not hold today. It says "every grok on PATH … reports grok 1.0.52" and "No 1.0.62 was ever observed". Re-running its own re-derive command now, two of the three PATH binaries print 1.0.62. The CHANGELOG head does say 1.0.52, so either the binary was upgraded after the operator's measurement, or the CHANGELOG lags the binary. The version-agnostic outcome is robust to this, so I applied it unchanged. The decision doc's "Premise found false" paragraph is itself now stale. The operator or orchestrator should re-word it; I did not edit it.

placeholder scan: precheck `[H-MAD] precheck grok-audit-surface.spec.md PASS issues=0`. The advisories are STALESHA, COUNT and PATH, on lines 27/32/35/39/79/130/178/197/286-290. All of them predate this revision and none is on a line I changed.

VERSION-HISTORY: OK version=v1.7 line=291 placement=append

owed by other documents:
- Plan and design: quote the D4 canonical sentence verbatim and drop every target grok version (concurrent authors).
- Design: no change is owed. The spec now matches its D1 last resort and its drift DECISION, and the design's "DECISION (design-author)" label on the smoke-commit descent can be re-labelled as spec-required.
- Decision doc: its 1.0.52 premise is contradicted by the current measurement (see above).
- AC-5.5 is unchanged. `not_descendant` now has three triggers, and the "each branch its own fixture" rule covers them. The design already lists `test_drift_score_not_descendant_of_smoke_commit`.

## Quotable ACs

D4:
> - **D4 Re-smoke (amended by operator decision, 2026-10-19: version-agnostic).** The re-smoke covers the AUDIT PATH ONLY. The host-mode adapter is out of scope. The audit-path re-smoke runs against the grok on PATH at S1, whatever its version; the smoke records that binary's path and its `grok --version` line, and the measurement doc names that version. No phase document names a target grok version. (Decision record: `docs/03-analysis/grok-audit-surface.decision-2026-10-19-d4.md`.)

Premises (tail of the grok-runtime bullet):
> This spec names no grok version for the audit path (D4): which binary is on PATH, and what its `grok --version` prints, is recorded by the smoke at S1, never stated here.

FR-1 heading: `### FR-1: Audit-path re-smoke on the recorded grok version (D4)`
FR-1 description fragment: "…and record what the audit path actually does on the grok on PATH, together with that binary's path and its `grok --version` line (D4)."

AC-1.5 fragment:
> …was re-smoked against grok `<version>`, where `<version>` is the version the smoke recorded from `grok --version` (D4), and naming the measurement doc.

AC-1.8 fragments:
> the audit path re-smoke against grok `<version>` failed, where `<version>` is the version the smoke recorded (D4), with the `reason=` values, naming the measurement doc.
> Each gains the measurement-doc pointer and one clause saying that the audit-path smoke on the recorded grok version failed.

Assumptions: "grok (whatever its version, D4) and agy are on PATH at calibration time."

AC-5.1 (replaces its final sentence):
> The smoke's token is `SMOKE:` (AC-1.7), whose unexpected failures map to its own two UNREADABLE reasons. The literal `SEEDSCORE: UNREADABLE reason=internal:<ExceptionName>` is the form for the score and rescore modes only; every other mode except the smoke carries `internal:<ExceptionName>` inside its own token grammar, which the design's per-mode token-grammar table names, so no mode prints two grammars.

AC-2.7 "Two shas, and the smoke commit" fragment:
> …and with `calibration_drift:not_descendant` when the later commit does not descend from the calibration sha, or when the score sha does not descend from the smoke commit (the score sha is required to descend from the smoke commit, not only from the calibration sha).

AC-5.4 bullet:
> - `calibration_drift:<path>` and `calibration_drift:not_descendant` (AC-2.7 "Two shas, and the smoke commit"). `not_descendant` covers both descent failures: the smoke commit or the score sha does not descend from the calibration sha, or the score sha does not descend from the smoke commit.
