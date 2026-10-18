DESIGN-AUTHOR: DONE version=v1.2 path=/Users/kimhawk/orca/skills/docs/02-design/features/grok-audit-surface.design.md lines=603 sha256=36f589e77a2a9960bd69fe762cae3a1a19057d88b694a9012af730d3e386de8c

Not committed. Ownership asserted before writing: mtime 1792366964, newest entry `- v1.1`.

## Changes
1. D4, version-agnostic.
   - D8 has a new "Re-smoke target" bullet. It quotes the canonical sentence from the decision doc verbatim.
   - D8 Versions: the first line of `s1/versions.txt` is now `grok_binary=<command -v grok> <that binary's --version line>`, or `grok_binary=absent`. The file is still three lines. The D3 layout and the six-exclusion reason were updated to match. No new file, so the exclusion count stays at six.
   - D11: `smoke` publishes `GROK-BINARY: path=<abs> version=<line>`, or `GROK-BINARY: unrecorded`. Like `wall_seconds.txt`, this is never a reason and never UNREADABLE, so AC-1.7's reason set and its UNREADABLE triggers are unchanged.
   - New opposed test pair in the smoke test module: `test_smoke_publishes_grok_binary_line` / `test_smoke_grok_binary_unrecorded_is_not_unreadable`.
   - D15 names the `GROK-BINARY:` line.
   - D14 smoke-failure clause, and the S3 doc test: "the grok <v> audit-path smoke failed". `<v>` is a slot filled from `GROK-BINARY:` (the first field after the leading `grok` of the `version=` line). Residual stated: if the line does not begin with `grok `, there is no `<v>` and the test fails.
2. Premise correction. No design line ever said python3 has pytest (grep for `3\.15` / `python3 (3.15)` / `has pytest` gave 0 lines before the edit), so there was no false line to fix. What I did instead:
   - Added three Readings rows: `python3` with `rtk proxy`, the anaconda interpreter, and `rtk rewrite`.
   - Added a 5e-precondition sentence explaining why the precondition never uses bare `python3`.
   - Every `python3 …` command in the design runs a stdlib script. The harness and `h_mad_resolved_model.py` do not import pytest (grep of their imports gave 0 lines). So no command needed re-pinning.
3. Token-grammar note. The design has no "reading of the spec, announced" note: grep for `reading of|announce` gave 0 lines. Spec v1.7 is not committed: `git log -1 -- spec` is still 94a4fd2c, though the spec is dirty in the working tree. I added nothing. The D2 table is unchanged.

## Premises verified
- `rtk proxy python3 -m pytest --version` printed `/opt/homebrew/opt/python@3.15/bin/python3.15: No module named pytest`.
- `rtk proxy python3 --version` printed `Python 3.15.0`; `command -v python3` printed `/opt/homebrew/bin/python3`.
- `rtk proxy /opt/anaconda3/bin/python3.11 -m pytest --version` printed `pytest 9.1.1`. `rtk proxy python3.11 -m pytest --version` printed the same, and `command -v python3.11` gave `/opt/anaconda3/bin/python3.11`. So the existing python3.11 Readings row holds.
- `rtk rewrite 'python3 -m pytest --version'` printed `rtk pytest --version`. `rtk rewrite` on the absolute anaconda form and on `python3.11 -m pytest` printed nothing (exit 1), meaning those forms are not rewritten.
- `which -a grok` loop:
  - `/opt/homebrew/bin/grok: 1.0.1`
  - `~/.grok/bin/grok: grok 1.0.62 (1474f9cbdd91) [stable]`
  - `~/.local/bin/grok: grok 1.0.62 (1474f9cbdd91) [stable]`

## Tree contradicts brief or decision doc
- **The decision doc's measurement is now false.** It says every PATH grok reports 1.0.52. At abe47752, both `~/.grok` and `~/.local` report 1.0.62 (1474f9cbdd91), so grok has evidently updated since then. This does not undo the decision (version-agnostic still holds, and is stronger for it). But the "No 1.0.62 was ever observed" premise in `docs/03-analysis/grok-audit-surface.decision-2026-10-19-d4.md` is now wrong. Whoever owns that doc should re-stamp it.
- **I replaced a Readings row, which goes past "no other changes".** The old row `grok --version` → `grok 1.0.52` @94a4fd2c was false at HEAD. Re-stamping it would put a literal version back into the body. I replaced it with a per-binary PATH reading that writes no version (@abe47752). Revert offered if the orchestrator prefers to keep the old row.
- **The brief's claim that the hook rewrites `python3 -m pytest` did not reproduce in the Bash tool.** A bare `python3 -m pytest --version` inside a compound command printed No module named pytest. `rtk rewrite` does show the rewrite, so I stated the hazard as "can rewrite".

## Sweep
- `grep -n '1\.0\.62\|1\.0\.52'` on the design gives 0 lines, Version History included (the v1.2 entry says "the literal version").
- `grep -n -i 'python3 (3.15)\|3\.15'` gives 1 line: the new Readings row, which is correct.
- `grep -n -o 'grok [0-9][0-9.]*'` gives only the `grok 9.9.9` fixture, on one line.

## Tools
- Version History: `VERSION-HISTORY: OK … version=v1.2 placement=append`.
- Precheck: `PRECHECK: PASS issues=0`. All advisories are existing ones:
  - PATH-new advisories: these name files the feature creates.
  - STALESHA at the 94a4fd2c rows.
  - COUNT at the D4 ledger line and the D14 heading line, neither touched by me.

## Owed by other documents
- **Spec/plan:** AC-1.5 / AC-1.8 should name the recorded version, per D4. Those docs are being revised concurrently.
- **Spec AC-1.7:** if the spec wants `GROK-BINARY:` listed among the smoke's published lines, it should add it. The design keeps it out of the reasons and the UNREADABLE triggers.
- **Plan:** the S1 runbook step that produces `versions.txt` should use the D8 command. The two new smoke test names are additions the plan's test inventory may need.
- **Mutation spec rows:** none were added for the `GROK-BINARY` line, because it is not a guard. Round 2 audit may want to judge that.
- **Decision doc:** its 1.0.52 measurement is stale (see above).
