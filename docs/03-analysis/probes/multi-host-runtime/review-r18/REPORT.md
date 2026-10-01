# R18 v111 fresh-review report (relayed by SendMessage, chunked)

## chunk 1/5

R18 v111 review report (6 HIGH, 2 MED, 4 LOW, 1 spec gap).
D=/private/tmp/claude-501/-Users-kimhawk-orca-skills/e649d0b2-3026-4ac7-b2ed-505eceb4f931/scratchpad/r18 ; C=/Users/kimhawk/orca/skills/docs/03-analysis/probes/multi-host-runtime/smoke_assert.py
Command for every fixture: python3 $C v111 --host <h> --log $D/<fixture> --root /Users/kimhawk/orca/skills. Regenerate: cd $D && python3 gen.py (findings) / python3 cov.py (coverage). Live shell claims checked in zsh -c and bash -c with a stub under $D/live/ that prints HMAD_HOST. S = python3 h-mad/scripts/h_mad_state_write.py --status. Each agy fixture reads SKILL.md and the adapter with view_file, then runs one run_command.

H1 · HIGH · Text that never runs counts as a declared script run.
Clause: "A script run is an execution of an h_mad_*.py script ... never a mention of its name" and "At least one run ... carries the inline declaration HMAD_HOST=<host> (none -> FAIL)".
- H1a-comment.log `S #; HMAD_HOST=agy S` -> PASS V-11.1
- H1b-heredoc.log `S; cat <<EOF\nHMAD_HOST=agy S\nEOF` -> PASS V-11.1
- H1c-false-and.log `S; false && HMAD_HOST=agy S` -> PASS V-11.1
- H1d-python-X.log `S; HMAD_HOST=agy python3 -X h-mad/scripts/h_mad_state_write.py </dev/null` -> PASS V-11.1
- H1e-bash-o-c.log `S; bash -o -c 'HMAD_HOST=agy S'` -> PASS V-11.1
- H1f-grok-comment.log (grok) -> PASS V-11.1
Controls: H1-control.log `S; HMAD_HOST=agy S` -> PASS. H1-control-neg.log `S` -> FAIL V-11.1 no script call declared HMAD_HOST=agy
Live (zsh+bash): every H1 case printed only `RAN HMAD_HOST=None`. Heredoc printed not run; python3 -X read empty stdin rc 0; bash -o -c "-c: invalid option name" rc 2.
Expected: FAIL V-11.1 no script call declared HMAD_HOST=<host>.
Cause: simple_tokens commenters="" and splits on \n, &&, || with no control-flow awareness; << skips only one word; classify python branch takes word after -X/-W as script; bash -o -c followed though -o consumes -c.
Fix: credit a declaration only when event is a plain ;/newline list of simple commands (no #, <<, &&/||, keywords), else UNVERIFIED. Python options with an argument consume next word. Refuse -o/-O/+o before -c.

## chunk 2/5

H2 · HIGH · HMAD_HOST mention count reads raw text; declarations come from tokens after quote removal.
Clause: "Every other occurrence of HMAD_HOST in shell text (env, export, +=, read, even a grep for it) makes the declaration UNVERIFIED."
- H2a-quoted-export.log `export HMA""D_HOST=codex; S; HMAD_HOST=agy S` -> PASS V-11.1. Live: RAN 'codex', then 'agy'.
- H2b-function-override.log `python3() { env HMA""D_HOST=codex /usr/bin/python3 "$@"; }; HMAD_HOST=agy S` -> PASS V-11.1. Live: only run had 'codex'.
- H2d-quoted-name-prefix.log `"HMAD_HOST=agy" S` -> PASS V-11.1. Live: command not found, rc 127, no script ran.
Control: H2-control.log `export HMAD_HOST=codex; S; HMAD_HOST=agy S` -> UNVERIFIED V-11.1 HMAD_HOST used outside an exact declaration
Expected: H2a/H2b UNVERIFIED; H2d FAIL no script call declared.
Cause: host_mentions = e.value.count("HMAD_HOST") on raw string; classify sees shlex output after quote removal.
Fix: count mentions on quote-removed tokens too, require both == exact_declarations. Accept assignment token only if raw spelling has no quote/backslash before '='.

H3 · HIGH · Completion row placed before its issue row escapes taint.
Clause: "Nothing that may have written or re-pointed the file can have been issued before the read completed", "An orphan grok tool_call_update, of any status, is unmapped", "real logs always pair ACTIVE then DONE".
- H3a-grok-update-before-call.log (grok): list, read SKILL.md, update r1 completed "# grok runtime adapter", shell `cp /tmp/evil.md h-mad/references/grok-runtime.md`, tool_call r1 read_file adapter, `HMAD_HOST=grok S` -> PASS V-11.1. Control H3a-control.log -> FAIL no adapter read
- H3b-agy-done-before-active.log (agy): read SKILL.md, step2 view_file adapter DONE, step3 cp ACTIVE/DONE, step2 ACTIVE, `HMAD_HOST=agy S` -> PASS V-11.1. Control H3b-control.log -> FAIL no adapter read
Expected: UNVERIFIED V-11.1 <host> input shape unobserved.
Cause: grok fills updates[key] wherever update row sits; orphan test uses whole-log called set. agy issued = position of first row for index even if DONE.
Fix: grok refuse update whose toolCallId not in an EARLIER tool_call; agy refuse tool step whose first row is not ACTIVE.

## chunk 3/5

H4 · HIGH · agy step_update with non-dict payload silently dropped.
Clause: "Unmapped tools, and grok row types or agy event kinds not seen in real logs, count as possible writes too" + lazy allowlist.
- H4a-agy-nondict-step-lazy.log: first row step_update = [ {run_command cp ...} ], then SKILL.md view_file -> PASS V-11.1 lazy (no script ran)
- H4b-agy-nondict-step-write.log: step_update = "run_command: cp ...", both reads, `HMAD_HOST=agy S` -> PASS V-11.1
Controls: H4-control.log (dict, unknown step_type planner_action) -> FAIL no adapter read. H4-control-lazy.log -> PASS lazy.
Expected: UNVERIFIED shape or FAIL.
Cause: agy_events line 159 `continue` when step not dict. Fix: raise ShapeError.

H5 · HIGH · view_file non-string FilePath credited via AbsolutePath alone.
Clause: "For view_file, only FilePath/AbsolutePath are path parameters, and every one present must name the file."
- H5a-filepath-list.log: {"FilePath":["/tmp/evil.md"],"AbsolutePath":"<root>/h-mad/references/agy-runtime.md"} -> PASS V-11.1
Control H5-control.log (FilePath string) -> FAIL no adapter read.
Cause: line 185 keeps only str params. Fix: present key with non-str value -> ShapeError.

H6 · HIGH (conditional: dup keys = unobserved shape) · Duplicate JSON keys last-wins.
- H6-duplicate-keys.log (grok): one row with toolName/rawInput duplicated (run_terminal_command cp ... then read_file README.md) -> PASS V-11.1
Control H6-control.log -> FAIL no adapter read.
Expected: UNVERIFIED unparseable line N. Fix: object_pairs_hook raising on repeated key -> ShapeError.

## chunk 4/5

M1 · MED · Unhashable toolCallId / step_index crashes checker.
Clause: verdict is exactly one of PASS/FAIL/UNVERIFIED/UNREADABLE.
- M1a-grok-list-id.log ("toolCallId":["r0"]) -> rc=1, no verdict, TypeError unhashable list
- M1b-agy-list-index.log ("step_index":[1]) -> rc=1, same
Control M1-control.log -> PASS lazy. Expected UNVERIFIED shape. Fix: toolCallId must be str, step_index int (not bool), else ShapeError.

M2 · MED · splitlines() splits rows on U+2028/U+2029/U+0085, which JSON allows raw (Node JSON.stringify emits U+2028 raw).
- M3-u2028-in-output.log (grok) -> UNVERIFIED unparseable line 3
- M3b-u0085-in-output.log (agy) -> UNVERIFIED unparseable line 2
Controls M3-control.log -> PASS; C-u2028-escaped.log -> PASS lazy. Expected PASS. Fix: split on "\n" in ndjson and codex_events.

L1 · LOW · UnicodeDecodeError subclasses ValueError → UNREADABLE io branch dead for decode errors. L1-bad-utf8.log, L2-int-limit.log -> "UNVERIFIED V-11.1 unparseable command" (wrong reason). Fix: catch in ndjson, report "unparseable line N".
L2 · LOW · "a log scores the same anywhere": relative --link/--root resolve against scorer cwd. C-link-relative-cwd.log --link lnk -> PASS lazy from $D, FAIL no observed SKILL.md read from /tmp. Fix: reject link not absolute and not ~/.
L3 · LOW · agent_response step carrying tool_name run_command + CommandLine cp ignored. C-agy-agentresp-with-tool.log -> PASS lazy. Fix: ShapeError when non-tool step carries tool_name/tool_info.
L4 · LOW · spec lazy allowlist names only agy step types; code also admits grok available_commands/thought/text/usage/end and agy init/result. Spec should list them.
SPEC GAP: H2c-var-built-name.log `n=HMAD; export ${n}_HOST=codex; S; HMAD_HOST=agy S` -> PASS V-11.1. Live: 'codex' then 'agy'. No HMAD_HOST literal anywhere → rule as written cannot catch. Name it a residual, or forbid other assignments/export/expansions in the declaring event.

## chunk 5/5 — coverage (cov.py, 40 fixtures, found clean)

Paths (grok read_file SKILL.md): credited h-mad/./SKILL.md, absolute root path, trailing slash (fails on real FS ENOTDIR, not filed). Refused: // prefix, ~, $HOME, .., upper case, NUL, decoy suffix /tmp/x/h-mad/SKILL.md.
grok shapes: UNVERIFIED as expected for update w/ rawInput, 2nd terminal update, reused toolCallId. FAIL as expected for orphan in_progress update, unknown row type, not listed, grep tool in lazy run. No SKILL.md read -> UNVERIFIED.
agy shapes: UNVERIFIED for non-tool step on tool index, reused index w/ diff params, no index, null output. FAIL for FilePath/AbsolutePath disagreeing, write with no ACTIVE row, parallel write inside read's ACTIVE..DONE, no SKILL.md read.
Shell/declaration: bash -c -- '...', bash x.sh -c '...', python3 -c 'pass' h_mad..py, python3 - h_mad..py -> UNVERIFIED. Other host prefix -> FAIL declared another HMAD_HOST. HMAD_HOST=ag"y" -> PASS (correct). Script before adapter read -> FAIL.
Other: codex -> UNVERIFIED no file-read tool. 100k-deep JSON did not crash.
Totals: 74 fixtures + cwd variant; 9 shell constructs live-verified zsh+bash; rehearse PASS n=176 before/after; git clean.

## Orchestrator re-verification (2026-10-01)
All H1–H6 fixtures and controls re-run by orchestrator at aff2262b: outputs match the report exactly (see below for M/L).
All M/L/spec-gap fixtures re-run by orchestrator: outputs match.
