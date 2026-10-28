DESIGN-AUTHOR: DONE version=v1.4 path=/Users/kimhawk/orca/skills/docs/02-design/features/grok-audit-surface.design.md lines=751 sha256=ad479bcff06020ded509183ba9ddee2f35847d853b1ff5ae1882b3a5e15c7c09

Not committed. Sole author; mtime/newest `- v1.N` asserted before the first write (1792369933, v1.3). PRECHECK: PASS issues=0. The remaining advisories (COUNT at D4 "4 fields", COUNT "2 sites" at the doc-test paragraph, STALESHA `94a4fd2c` in Readings) were all present on v1.3 at HEAD; I re-ran precheck on `git show HEAD:` to confirm. VERSION-HISTORY: OK version=v1.4 placement=append.

## Per finding: change, then the check that confirms it

### Must 1: drifted log must FAIL (repair (a))
- D11 step 3: an absent item refuses. A wrong-file rendering refuses: `p1 unreadable (log named…` (missing, empty) and `p1 not measured (codex-text log` (codex-text). Three forms fall through, each matched positively: positive grok, truncated, and the new "non-grok counts" regex `^p1 tools=\d+ ok=\d+ failed=\d+ thinking=\d+( |$)` (parsed, unparseable). Any other rendering refuses as well (none exists today). So over today's renderer the step refuses exactly as the brief specifies. That is my addition to keep the rule positive; drop it if you want "only" to be literal.
- Replaced the AC-1.1 sentence. A non-grok item that is not a wrong file now FAILs: truncated through `truncated`, and counts items through `vocab_missing`. For `unparseable` this is guaranteed: no `_GROK_TYPES` type was seen, and end, tool_call and tool_call_update are all members.
- Residual, stated exactly with two members. (1) A `parsed` item on a log that holds all three types. (2) An `unparseable` item whose grok-typed events `scan_grok` skips because they nest deeper than GROK_MAX_DEPTH=64 or raise RecursionError, while the smoke's step-2 type reading still counts them. Each has a residual-pin fixture that asserts `SMOKE: PASS`.
- The four opposed UNREADABLE fixtures are replaced:
  - Two drifted-log FAIL fixtures (unparseable, parsed). Each asserts the exact `vocab_missing:end,vocab_missing:tool_call,vocab_missing:tool_call_update` reason.
  - Three wrong-file fixtures (codex-text, missing, empty). They keep the synthetic f0_text pairing, and the design says why: step 2 refuses a real wrong file first.
  - Two residual pins.
- Swept the M3 row and the `truncated` bullet ("Step 3 has already refused…").
- Checks, run against the real functions with `rtk proxy /opt/anaconda3/bin/python3.11`; the inline scripts left no files behind.
  - Three `{"type":"response.*"}` lines give shape `unparseable`. Adding `{"event":"init"}` gives `parsed`. Both render `p1 tools=0 ok=0 failed=0 thinking=0 low-evidence (…)`.
  - parsed with all three types gives `parsed`.
  - Three 65-deep lines give `unparseable`, with type set {end,tool_call,tool_call_update}. So residual (2) is real, not reasoned.
  - empty and missing both render `p1 unreadable (log named but not readable)`. codex-text renders `p1 not measured (codex-text log; …`.
  - The counts regex matches the rendered line.

### Must 2: `--reset` validates before any removal ((a)+(c))
- D5 gains a five-guard precondition that runs before step 1 and before any write or removal:
  1. isabs. The empty string fails here.
  2. isdir.
  3. Resolved parent == `Path(tempfile.gettempdir()).resolve()`.
  4. Resolved basename starts `gas-root-d<k>-s1-`.
  5. D7 reach on the target, giving `root_git:<path>`.
- Refusal reasons are a DECISION, justified in the design. Guards 1–4 use `internal:<E>`, with one class per guard: ResetTargetNotAbsolute, NotDirectory, OutsideTempdir, Prefix. `root_git` would falsely claim a repository at a mistyped `$HOME` or out-of-tmp path. One class per guard is my addition: it makes each P-row discriminate. Under a single class, a guard that was disarmed and fell through to its sibling would print the same token, and the mutant would survive.
- I also dropped a "not a symlink" sub-clause that had no fixture. Guard 3 already judges a symlink by its target.
- `--reset`/`--dest-parent` exclusivity is now checked by the mode and not by argparse: `internal:ResetArgsConflict`, marker GAS-RESET-EXCLUSIVE.
- Fixtures and P-rows (the P-row list is written out in the mutation-spec section):
  - The brief's three: a git-init'ed `gas-root-d1-s1-` dir under the tempdir giving `root_git:.git`; the empty string; a dir outside the tempdir.
  - Plus a missing target and another document's prefix.
  - Each fixture asserts its sentinel survives.
  - One must-not-refuse fixture: the `pwd -P` spelling.
- Runbook: `[--reset "${ROOT:?}"]` (2 sites, both swept), plus a sentence on what it stops. Error Handling now lists D5 under `root_git`.
- Fix-introduced defect, caught and repaired: with the new precheck, `test_build_root_reset_runs_the_reach_check` (a `.git` planted before the call) would have been caught by guard 5 rather than step 6. It now plants `.git` from inside the patched removal step, so only step 6 can see it.
- Check: I ran the `${ROOT:?}` and `pwd -P` path forms in a shell. `mktemp -d` gives `/var/folders/…/T/tmp.X`, and its `pwd -P` form is `/private/var/folders/…`.

### Must 3: X1/X2 over the split wire (repair (a))
- D12 has a 5-line python block: `found = report_findings(text)`, `must, should = …`, `_counts = _gate.classify(text)` (unmarked), then `must_count = _counts["must_count"]  # M:GAS-MUST-COUNT-WIRE` and `should_count = _counts["should_count"]  # M:GAS-SHOULD-COUNT-WIRE`.
- X1 replaces the must line with `len(must)`. X2 appends ` + 1` (int + 1, not a crash kill).
- New X5/X6 do the same to the should line. Both target `test_should_findings_are_written_on_a_count_difference`, which now asserts the exact `gate=<n+1>` line, so X6's `gate=<n+2>` kills.
- Swept the M6 row, the D12 "X1/X2 on the count" phrase, the Rows preamble (X1–X4 → X1–X6) and the compliance list.
- Check: I extracted fenced blocks with `awk '/^ *```/{inb=!inb; next} inb'` (16 fence lines, so 8 blocks) and ran `grep -cF`. Must find: 1. Should find: 1. `_counts = _gate.classify(text)`: 1. Whole document: must find 2 (the block plus the X1 row, as intended). My first awk used `/^```/`, missed the indented fence, and gave 0/0. I corrected it before relying on the number.

### Should 1: renderer pin covers seven shapes
- The pin derives the shape set from `inspect.getsource(measure_effort)` with the regex `"shape"\]?\s*[:=]\s*"([a-z-]+)"`, asserts the seven, and maps each shape to its step-3 form.
- Check: running that regex gave ['codex-text','empty','grok','grok-truncated','missing','parsed','unparseable'], which is 7 distinct values.

### Should 2: tests for the two missing reset guards
- Added `test_build_root_reset_mismatch_is_internal` (re-walk patched to report an extra path) and `test_build_root_reset_and_dest_parent_are_exclusive`, with P-rows GAS-RESET-REWALK and GAS-RESET-EXCLUSIVE.

### Should 3: agy log selection
- The selection now matches both spellings: `ROOTP=$(cd "${ROOT:?}" && pwd -P)` and `grep -qF -e "workspaceDirs=[$ROOT]" -e "workspaceDirs=[$ROOTP]" -- "$f"`. The UNKNOWN echo names both.
- The `exec agy --cd "$T"` tracer before S1 is a Phase-5 step, in D8 and in Implementation Order step 11. I did not run it.
- Check: I ran the two-pattern grep with each spelling alone and with `workspaceDirs=[/]`: match, match, no match. `_cmd_exec` accepts `--cd` (hmad-dispatch.sh `_cmd_exec` signature comment).

### Should 4: needles are per-line payloads
- D3 (c) needles are now the normalised `_gate._payload` of each finding's bullet line, and of each line of a prose-only finding. Continuation lines and nested evidence bullets are not needles.
- The residual is restated, including its fail-closed side: short payloads over-include.
- The finding-text fixture now plants only the payload.
- Check: `grep -n 'def _payload' h-mad/scripts/h_mad_audit_gate.py` found it, and it was already in D1's import list.

### Nits (all four done)
- "(negative control: …)".
- "10 to 19 dispatch roots", which matches the plan text exactly (grepped).
- The agy block's placement before the codex block.
- An M1/M2 no-row sentence. Counted by a python regex over the Gate pins and Wrapper pins sections: 15 distinct test names, 14 of them row targets. The reviewer said 16 of 17; their corpus may have been wider. The claim as written holds over these two sections.

## Sweeps
`grep -nF` for: 'six shapes', 'must_count=_gate', 'ResetTargetRefused', 'X1–X4', 'ten or more', '[--reset "$ROOT"]', 'agy_shape', 'must not include', 'whole normalised text', 'refuses neither', 'nothing else reaches the reasons'. All return 0 lines. 'workspaceDirs=[$ROOT]"' appears once, at the intended two-pattern grep. History lines v1.1–v1.3 were left as written.

## Tree contradictions
None with the spec or plan. The review cites `_CODEX_BANNER`. The design's `_CODEX_HEADER_RE` is the name defined in h_mad_review_evidence.py, and my measured codex-text log matched it.

## New, for Phase 5 (not fixed)
1. Argparse usage errors (unknown flag, missing required argument) exit 2 with a usage line and no token. AC-5.1 says "every path out". `test_internal_failure_prints_the_mode_token` does not cover SystemExit from argparse. The design never mentions argparse except in the v1.4 exclusivity sentence.
2. `--reset` with a `--purpose` other than `s1` is not refused. The guard-4 prefix is the literal `s1`, so an s1 root reset with `--purpose s2v1` passes and rebuilds under the s1 name. Decide whether `--reset` requires `--purpose s1`.
3. Step-3 wrong-file guard: its fixtures need a synthetic pairing because step 2 shadows it on real inputs. It is defence in depth, and whether it is reachable at all depends on record-cycle copying exactly the file the wrapper measured.
4. The residual (2) fixture uses 65-level nesting. If `GROK_MAX_DEPTH` changes, the fixture needs depth `GROK_MAX_DEPTH + 1`; derive it from the constant.

## Owed by other documents
None required. The plan's "10 to 19" now agrees with the design.
