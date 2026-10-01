# R19 v111 fresh-review report @99679c5f (relayed by SendMessage, chunked)

## chunk 1/4

R19 v111 @99679c5f — 3 HIGH fail-open classes, 1 HIGH needs operator spec decision, 2 MED, 1 LOW.
Fixtures: scratchpad r19/logs/<id>.log; generator r19/mk.py. Every agy log: view_file SKILL.md + view_file agy-runtime.md (heading outputs) then shown run_command. Stub r19/stub/h-mad/scripts/h_mad_state_write.py (755) prints "RAN HMAD_HOST=$X". Live = `zsh -c` and `bash -c` with stub dir cwd. P = h-mad/scripts/h_mad_state_write.py. Baseline rehearse PASS n=219.

H1 · HIGH · python3 options that never run the script
Clause: spec l.730 "A script run is an **execution** of an h_mad_*.py script". classify(): any short cluster w/o c/m/W/X lets next word be the script operand.
- F1a-py-V `HMAD_HOST=agy python3 -V P` → PASS V-11.1. Live zsh+bash: "Python 3.14.7", no RAN.
- F1b-py-h `python3 -h P` → PASS. Live: usage, no RAN.
- F1c-py-VV `python3 -bV P` (clustered) → PASS. Live: version only.
- F1d-py-badopt `python3 -z P` → PASS. Live: rc=2 "Unknown option: -z".
- grok F1-grok-V → same PASS.
Expected: UNVERIFIED (not plain) or FAIL no script call declared.
Control C2-py-b-control `python3 -b P` → PASS, live "RAN HMAD_HOST=agy" both shells.
Fix: positive allowlist — follow a cluster only if every letter in bBdEiIOPqRsSuvx (W/X as takers); anything else → unknown.

H2 · HIGH · bash/sh/zsh options before -c that suppress execution
Clause: same. Spec -c rule only excludes o/O, +, long.
- F2a-bash-n `HMAD_HOST=agy bash -n -c P` → PASS. Live both: rc=0, empty (noexec).
- F2b-zsh-nc `zsh -nc P` → PASS. Live: empty.
- F5-sh-n `sh -n -c P` → PASS. Live: empty.
- F2c-bash-D `bash -D -c P` → PASS. Live: empty (-D implies -n).
- F2d-bash-r `bash -r -c P` → PASS. Live: "restricted: cannot specify `/' in command names".
- F2e-zsh-r `zsh -r -c P` → PASS. Live: "zsh:1: …: restricted".
- F2f-bash-badopt `bash -Z -c P` → PASS. Live: "-Z: invalid option" rc=2.
- grok F2-grok-n → same PASS.
Controls: C1-bash-c-control `bash -c P`, C1b-bash-e-c `bash -e -c P` → PASS, live RAN agy. F2g-zsh-digit `zsh -1 -c P` ran live (control, not finding).
Fix: positive allowlist of short letters before -c (e.g. e u x v + c). Any other letter (n, D, r, invalid, digit) → unknown.

## chunk 2/4

H3 · HIGH · Empty/doubled separators: shell rejects the line at parse time, nothing runs
simple_tokens() treats a run of `;` as a separator and drops the empty command; the shell rejects the whole line first.
- F8a-dsemi `HMAD_HOST=agy python3 P;;` → PASS. Live zsh: "parse error near `;;'" rc=1; bash: "syntax error near unexpected token `;;'" rc=2. No RAN either.
- F8b-lead-semi `; HMAD_HOST=agy python3 P` → PASS. Live bash: syntax error, nothing runs; zsh: RAN agy.
- F8d-semi-semi-mid `ls ; ; HMAD_HOST=agy python3 P` → PASS. Same split.
F8b/F8d fail open only if host shell is bash; log does not record which shell run_command/run_terminal_command uses.
Not a finding: F8c (`P` newline `;`) — script runs in both before bash reports line-2 error.
Control F8-control `ls ; HMAD_HOST=agy python3 P` → PASS, runs live both.
Fix: in plain(), refuse `;;`, leading `;`, two separators with no word between (`;` `;`, newline `;`). Plain newlines and `;` newline fine.

H4 · HIGH (checker + spec gap; needs operator decision) · script operand never bound to h-mad
Clause l.730 "execution of an h_mad_*.py script", no path. Reads bound lexically to <root>/h-mad or --link; runs not.
- F6-decoy `HMAD_HOST=agy python3 nowhere/h_mad_x.py` → PASS. Live both: rc=2 "can't open file". Any /tmp/h_mad_fake.py same.
- Related LOW (text-only checker cannot know existence):
  - F3-module `HMAD_HOST=agy python3 -m h_mad_state_write` → PASS. Live "No module named h_mad_state_write". No adapter says use -m.
  - F9-py-missing `python3.99 P` → PASS. Live rc=127.
  - F4-zsh-eq `python3 =x/h_mad_state_write.py` → PASS. zsh `=` expansion aborts; bash python cannot open. Neither runs.
Fix: bind operand / direct invocation via names_file predicate: equals <root>/h-mad/scripts/<name> or <link>/scripts/<name> after lexical normalisation, refuse `..` and leading `=`. Drop -m to unknown. Amend l.730 to bind path like reads.

## chunk 3/4

M1 · MED · Apostrophe anywhere in shell text turns a read-based FAIL into UNVERIFIED
Clause: "A FAIL decided outside the declaration stays a FAIL: … for codex and agy, no skill read"; general "a script or dispatch before the adapter read FAILs", "anything unproven needed the adapter: FAIL".
Cause: main loop calls simple_tokens() on every shell event; shlex ValueError (unbalanced quote) escapes to outer handler → "UNVERIFIED V-11.1 unparseable command" before any read-based FAIL.
- M1a-noread-apostrophe: agy, no reads, one run_command `ls h-mad  # don't read yet` → UNVERIFIED unparseable command; expected FAIL no adapter read. Control M1a-control (`# do not read yet`) → FAIL no adapter read.
- M1b-noskill-apostrophe: view_file agy-runtime.md only, `HMAD_HOST=agy python3 P --status`, `ls docs  # what's here` → UNVERIFIED unparseable; expected FAIL no observed SKILL.md read. Control M1b-control → FAIL no observed SKILL.md read.
- Live: both shells accept the commented line rc=0.
Fix: catch ValueError per event in loop; treat event as one unknown command (mentions h_mad if MENTION matches raw). Already taints + fails plain(); read-based FAILs still run.

M2 · MED · Crash: deep rawOutput nesting overflows strings()
- X2-grok-deep2000.log: grok read_file SKILL.md, completed update rawOutput = 2000 nested lists around "x" → uncaught RecursionError at smoke_assert.py:60 (strings) from :163, exit 1, no verdict. Depth 500/900 ok; 5000 crash. agy never calls strings(). 100000-deep JSON row (X1-deep) ok (3.14 json non-recursive).
Fix: iterative strings() with stack, or catch RecursionError → ShapeError("grok output shape unobserved").

L1 · LOW · A blocking safe command keeps the declared script from running
F7-tail-f `tail -f /dev/null; HMAD_HOST=agy python3 P` → PASS. Live times out. `cat` with no arg same. Hosts usually kill hung commands. Fix: refuse -f/-F/--follow for tail; refuse cat/head/tail/nl/grep/wc with no file operand.

General note: v111 never checks the declared script's shell event succeeded. Backstop: require ≥1 declared script event with success=True (and non-empty output where recorded). Would not catch H1/H2 (-V/-h print).

## chunk 4/4 — coverage, probes with no finding

Dedup: grepped review-r18/REPORT.md, live-smoke addendum, spec for -V, -h, -n, noexec, restricted, ;;, decoy, recursion, unparseable command, apostrophe — none of H1–H4, M1, M2 reported earlier.
Correct/conservative (no finding):
- \r outside PLAIN_TEXT. Single `;`, newlines, trailing `;`, tabs same in shlex and both shells.
- `HMAD_HOST+=agy` unknown/not plain; `HMAD_HOST=agy:x` fails DECLARATION. zsh `=python3` command → unknown; as operand → H4.
- Two declaration values → FAIL another HMAD_HOST; bare `HMAD_HOST=x` line → UNVERIFIED (mention mismatch); `bash -c HMAD_HOST=grok` → UNVERIFIED; prefix assignment to safe command → UNVERIFIED.
- Keywords fi/then/time unknown → not plain.
- python -W/-X takers, -Wd, -c/-m in cluster, `-`, long options per spec; python3.N regex correct.
- Path-qualified interpreters (.venv/bin/python3): plain cmds cannot create one after reads → trusted env.
- hmad-dispatch only for ordering, not declaration, per spec.
- Safe set GNU/BSD: no plain arg writes/executes; sed_safe holds; blocking = L1.
- grok update-before-call → shape; orphan update = unmapped other issued=0 (conservative).
- agy ACTIVE/DONE/ACTIVE/DONE on one index accepted; completed = LAST DONE (conservative). A1-agy-double-done → FAIL. Identity mismatch → shape. Non-tool check, tool_steps & other_steps hold. unique_keys nested incl. escaped keys.
- Codex early return.
Fixtures: 42 logs in scratchpad r19/logs/ (r19/mk.py, stub r19/stub/). Controls: ctrl, C1-bash-c-control, C1b-bash-e-c, C2-py-b-control, F2g-zsh-digit, F8-control, M1a-control, M1b-control. No tracked edits.
