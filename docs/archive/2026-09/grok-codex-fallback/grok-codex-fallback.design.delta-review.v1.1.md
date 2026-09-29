## Summary
ADVISORY delta review of the design v1.0 to v1.1 diff (`96eeed4`). I read it against both cycle-1 audit reports, spec v1.3 (`0df3d47`) and the tree. The `h-mad/` tree is identical at `50560eb`, `0df3d47` and `96eeed4` (`git diff --name-only … -- h-mad handoff | wc -l` gave 0 files for both pairs).

Every cycle-1 finding in both reports has a hunk that closes it. Many of the stated numbers re-derive exactly:
- 188 anchor rows, split 91/44/10/39/4/0/0 (unit: mutation rows). All 188 match their file exactly once today.
- 58/58 AC ids.
- 5 shape lines.
- 89 lines in the AC-4.10 fixture.
- `STATUS: DONE` and `2 tool calls completed; last tool: search_replace completed` on F0.
- The P8 mutant printing `2`.
- The D2 pipefail exit 5.
- The shell and Python banner windows agree at the byte-4096 edge.

Executing the hunks found one new real defect: `_grok_region_state`'s early exit takes SIGPIPE under `pipefail`. There are also several prescription and row-level gaps. I found nothing that breaks an invariant outright.

The tool-absent farm deviation is sound on this host. No second `jq` is reachable: `/bin` has none, the wrapper adds no PATH element, and `command -v` is the same predicate the code uses. The residual channels are listed below.
Evidence: 17 files opened, 41 greps run.

## Must-fix
None

## Should-fix
- `_grok_region_state` reports `jqfail` ("jq failed") when jq did not fail. The design sells the early exit as a feature, but the program reads a pipe from `_grok_region`'s `tail`, and its rc is captured under `set -o pipefail`. When `jq` stops at the first `end` while `tail` still has more than a pipe buffer to write, `tail` dies of SIGPIPE and the pipeline exits 141. I executed this under `/bin/bash` with `set -euo pipefail`, `_grok_region` as designed, and the design's program:
  - an `end` line followed by 20,000 `thought` lines (1,420,039 bytes) gave `st=complete rc=141` in 3 of 3 runs;
  - a 21,315-byte control gave `rc=0` in 3 of 3 runs.

  Under the D3.5 rule "exited non-zero → `jqfail`", a completed run with trailing data after `end` takes the EMPTY path and prints `grok stream not parsed — jq failed`. The direction is a false cannot-judge, and the stated cause is false. On F0, `end` is the last line, so no fixture exercises this. Repairs, any of which works:
  - (a) drop the short-circuit and consume the whole region, e.g. `reduce (inputs|…|select(.type=="end")) as $_ (false; true)`. This matches the other three helpers, which already read everything;
  - (b) judge `jq`'s own status from `${PIPESTATUS[1]}` instead of the pipeline rc;
  - (c) make `_grok_region` tolerate SIGPIPE.

  The same hazard applies to any early-exit consumer whose pipeline rc is captured. I checked the other new pipelines: `_grok_log_has_events` reads the file directly, `_grok_final_message`, `_grok_stop_reason` and `_grok_last_tool` reduce all input, and D5 slurps. So this is the only member today. The repo already has a SIGPIPE precedent in `h-mad/tests/mutation-specs/agy_recovery_sigpipe.json`.
  class: build
  quote: docs/02-design/features/grok-codex-fallback.design.md › `and it stops at the first `end`. Its rc is captured (`st="$(…)" || rc=$?`) rather than masked, so`
- Row D2's `find` matches nothing in the design's own fallback grep. The design spells the fallback as a double-quoted bash string: `grep -aqE "^[[:space:]]*\{.*\"type\"[[:space:]]*:…"`. The file will therefore contain `\{.*\"type\"`, with a backslash before each quote. The row gives `find` `\{.*"type"` and `replace` `\{[[:space:]]*"type"`. I copied the design's fallback into a script under the scratchpad and counted: `grep -c '\\{\.\*"type"'` gives 0 matching lines and `grep -c '\\{\.\*\\"type\\"'` gives 1. An implementer who transcribes the row gets an anchor that matches 0 times. Repair: give the row's find as `\{.*\"type\"` and its replace as `\{[[:space:]]*\"type\"`, matching the source bytes. The fallback grep itself behaves as claimed: `{"meta":1,"type":"text","data":"x"}` gives grok, while `…"type":"bogus"…` and `…"type":"tool_callx"}` give not.
  class: build
  quote: docs/02-design/features/grok-codex-fallback.design.md › `| D2 | `_grok_log_has_events` fallback | `\{.*"type"` → `\{[[:space:]]*"type"` (first-key only) |`
- §"Existing mutation anchors" rule 2 understates the collision rule. The harness counts substrings (`h-mad/scripts/h_mad_mutation_harness.py:753` `hits = source.count(find)`). A single-line anchor is therefore matched by any new line that contains it at the same or deeper indentation, because the anchor's leading spaces are a suffix of the deeper indent. Take `        if effort["ok"] <= DELIVERY_FLOOR:` (8 spaces, `audit_effort.json`): a grok branch in `_effort_items` that writes the same test at 12 spaces makes it match twice. So "verbatim" should read "as a substring".

  Two of the four near-collisions carry no prescription: the `scan_grok` thinking sum and `grok_from_log`. "widening the shape test in front of them" has nothing to widen in either target:
  - in `combine()` (h_mad_audit_cycle.py:871–883), the only shape tests before the floor line return or `continue`;
  - in `_effort_items` (h_mad_audit_cycle.py:625–634), the only shape test before the floor line is the anchored `codex-text` `continue`.

  The executable form is a new guard before each floor line, e.g. `if shape not in ("parsed", "grok"): return … shape_unrouted`, plus a `line = …` chosen by shape. Rule 1's list also omits the two other `codex_log_not_measured.json` anchors in those same edited functions: `        if shape == "codex-text":` (line 871) and `        if effort.get("shape") == "codex-text":` (line 625). The design edits both functions, so both belong on the "kept" list.
  class: build
  quote: docs/02-design/features/grok-codex-fallback.design.md › `2. **No new code reproduces an anchor verbatim**, since a second copy makes the anchor match`
- The farm is sound here, but reusing the existing runner defeats it, and the design does not say so. `_isolated_env` in `test_hmad_dispatch.py` (lines 120–165) runs `e.update(env)` and then unconditionally sets `e["PATH"] = f"{bindir}:/usr/bin:/bin"`. `run()` (line 166) goes through it. A farm cell that passes `_BINDIR=<farm>` to `run()`, as every existing exec test does, therefore runs on `<farm>:/usr/bin:/bin`, where `/usr/bin/jq` resolves. The design notes only that `_bindir()` links jq.

  The precondition catches this, but only if it is evaluated in the env the wrapper actually receives, not in a separately built dict. Repair: state that farm cells call `subprocess.run(["bash", WRAPPER, …], env=…)` with their own env, not `run()`/`_isolated_env`, and that the precondition runs in that same env.

  I checked the other channels for a second `jq`:
  - `ls /bin` has no `jq` or `grok`;
  - `hmad-dispatch.sh` and `bin/hmad-dispatch` set no `PATH`, have no `path_helper` or login shell, and call no absolute-path `jq`;
  - `_cmd_exec` (lines 2737–3207) and the progress path call no `jq` and no `python3` directly;
  - `BASH_ENV` and `ENV` are empty in this session.

  Unverified residuals worth one line each:
  - a cell env copied from `os.environ` inherits any ambient `BASH_ENV`, which a non-interactive `bash` sources and which could extend PATH;
  - on a merged-`/usr` host, `/bin` is `/usr/bin`, so every farm cell errors on its precondition. That is loud, not vacuous, but it is a portability limit.

  The deviation itself (all of `/usr/bin` minus the tool, 932 entries here, versus an enumerated `_WRAPPER_TOOLS`) is justified as written.
  class: build
  quote: docs/02-design/features/grok-codex-fallback.design.md › `The cell's PATH is exactly `<farm>:/bin`.`
- Row E5 does not reliably kill its mutant. The window-edge log is specified only as "a first line long enough that the banner starts past character 4096". The mutant `CODEX_BANNER_HEAD = 8192` is killed only if the banner line starts at or before character 8178 (8192 minus 14 for `OpenAI Codex v`). A longer first line leaves the mutant alive.

  The same unbounded fixture is also the only thing that pins the shell's `head -c 4096` in the format-agreement test. That makes a third spelling of the window, and it has no mutation row. The "written twice" count covers only the two Python spellings.

  Repair: fix the banner start at a stated offset in 4083..4178, e.g. directly after a 4095-character first line, so it is just outside 4096 and inside any window of 4192 or more. Also add a row for the shell `head -c 4096` → `head -c 8192`, killed by the format-agreement test on that log. I executed the edge: the shell and Python agree yes at a banner start of 4082 and no at 4083, 4084 and 4096.
  class: build
  quote: docs/02-design/features/grok-codex-fallback.design.md › `The window `4096` is written twice because one copy is a committed mutation anchor`
- The `_grok_region_state` program as given prints JSON strings. I executed `jq -nR '<the program>'` on F0 and it printed `"complete"`, quotes included. D3.5 specifies `-r` only for `_grok_final_message` (`jq -nR -r`). Every other helper is `jq -nR …`. Under the four-word contract, anything that is "neither `complete` nor `truncated`" is `jqfail`, so a literal transcription reports `jqfail` on every run. `_grok_last_tool` and `_grok_stop_reason` need `-r` for the same reason: the printed line would otherwise carry quotes. AC-4.10's `contains` would still pass on the quoted text, which hides the difference. Repair: spell the invocation as `jq -nR -r` for all four helpers.
  class: build
  quote: docs/02-design/features/grok-codex-fallback.design.md › `The program is`
- The `RecursionError` catch is not exercised by the planned test on every interpreter, and no mutation row covers it. The malformed-`type` test uses a line nested 5000 deep. I executed `json.loads` on an object nested n deep:
  - Python 3.11.8: `RecursionError` at 1000, 5000 and 200,000;
  - Python 3.14.7 (this host's `python3`): parses at 1000 and 5000, and raises only at 200,000.

  Under 3.14, deleting `RecursionError` from the `except` tuple therefore survives the test. The harness commands use `python3.11`, which is the only thing keeping the test live today. This also makes one member of D4's measured disagreement class ("nesting 5000 deep … Python 3.11 raises") interpreter-dependent. Repair: use V15's 200,000 depth in the test, and add a row `(ValueError, RecursionError)` → `ValueError` killed by it. This is an instance of: exceptions `scan_grok` must absorb. The rule is "every exception `json.loads` can raise on one line is caught". The residual is exception types not yet measured, such as `MemoryError` on a huge line.
  class: build
- The class-sweep command does not produce the population the text attributes to it. The design says the grep finds the banner in the three classifiers "plus two non-members", naming `h_mad_archreview_cycle.py` first. I ran the exact grep, and its matching lines fall in three files only: `hmad-dispatch.sh`, `h_mad_audit_cycle.py` and `h_mad_review_evidence.py` (5 matching lines each). `h_mad_archreview_cycle.py` has 0 matching lines. Its membership, via `from h_mad_review_evidence import scan` at line 117, is correct but was found some other way.

  More importantly, a banner-keyed needle cannot see a content classifier that keys on `scan()`/`agy_events` alone, and that is exactly the shape of `h_mad_archreview_cycle.py`. The "re-run the grep above at 5g" residual is therefore blind to the member it names. Repair: widen the needle to `from h_mad_review_evidence import\|agy_events\|_exec_log_format\|OpenAI Codex`. At this tree that finds exactly `hmad-dispatch.sh`, `h_mad_audit_cycle.py`, `h_mad_review_evidence.py` and `h_mad_archreview_cycle.py` under `h-mad/scripts`, excluding `__pycache__/*.pyc` (unit: source files).
  class: measurement
  quote: docs/02-design/features/grok-codex-fallback.design.md › `finds the banner in exactly the three classifiers above, plus two non-members:`
- The Error Handling claim "A read failure is BLOCK-INVALID `<unreadable>`" now contradicts D2's own new paragraph. D2 shows a failure on the first (`ACTIVE`) read exits the hook with rc 5 rather than a BLOCK. I re-ran it: `{"orchestrator_state":{"a":{"phase":"step5"},"b":3}}` under `set -euo pipefail` exited 5 without reaching the next line. So the sentence holds only for the second read. Whether rc 5 blocks or allows a PreToolUse tool call is not stated anywhere I checked (unverified). Repair: scope the sentence to "a failure of the `fallback_agent` read". Then either state the first-read rc-5 outcome as a pre-existing residual with its fail direction, or leave it out of scope explicitly.
  class: measurement
  quote: docs/02-design/features/grok-codex-fallback.design.md › `A read failure is BLOCK-INVALID `<unreadable>`,`

## Nit
- The new mutation rows `D1` and `D2` reuse the names of sections §D1 (schema) and §D2 (gate). "row D2" in the Test Strategy and "(D2)" in V16 then point at different things. Consider `L1`/`L2` for the log-format rows.
- W1's residual says grok "is installed at `~/.grok/bin/grok`". `which -a grok` here also lists `~/.local/bin/grok` and `/opt/homebrew/bin/grok`. The conclusion (none on `/usr/bin:/bin`, `command -v grok` rc 1, re-executed) holds.
- The farm helper should say that a stub name wins over a same-named `/usr/bin` entry, or `symlink_to` raises `FileExistsError`. No current stub (`agy cmux codex lsof orca`) collides with `/usr/bin` on this host.
