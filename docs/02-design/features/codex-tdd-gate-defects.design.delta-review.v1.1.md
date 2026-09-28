## Summary
This is an advisory delta review of eec0c7a6..037c9f6b (design v1.1, spec v1.4, plan v1.3). Every codex p1 must, and every teammate must and should, is closed by a hunk that addresses the class and not only the instance named. I checked each tree premise the delta leans on, and each one held when re-run:
- AC-6.9's "today rc 5" (all 4 writes rc 5, 0 stderr bytes);
- the DD-7 old-gate count (5 of 18 active cells refused);
- today's `_suite_summary` readings on the 5 new rows;
- `KNOWN_TYPES`: 11 entries, all matching `C`;
- `_pct_decode` round-trip under /bin/bash 3.2;
- Task 12's text as D13 describes it.

What remains is propagation drift between the three documents, plus gaps in the D13 contract and in D9's stdin rule. None of it is a hard gate. D13 is enough to start re-planning grok Task 12, but not enough to execute that re-plan unaided.
Evidence: 17 files opened, 16 greps run, 7 scratch executions (old-gate probes ×2, `_suite_summary`, D7 regex, `KNOWN_TYPES`, `_pct_decode`, nested-venv build).

## Must-fix
None

## Should-fix
- The D9 stdin reader falls back to `$1` in cases the spec says must not consult `$1`, and the design contradicts its own rationale on this.
  - Spec FR-6 (and the plan's layer 6, step 0, copied verbatim) says a failed stdin read is no target and `$1` is not consulted.
  - Design D9 step 2 sends three cases to the `TRC == 0`, `TP` empty branch, which then takes `$1`: a non-JSON payload, a truncated payload (the 2.0 s bound hit mid-payload, then JSON parse fails, then exit 0), and a held-open pipe with no data.
  - The design's own error-table row says a payload that is "present but unusable" must not consult `$1`. A non-JSON payload is exactly that, yet it falls back to `$1`.
  - instance of: the set of stdin outcomes {empty, not an object, no field, control char, parse failure, timeout with 0 bytes, timeout with partial bytes, reader exception}.
  - Rule over the set: exit 0 with empty output only when 0 bytes were read (EOF or tty). Exit non-zero when any byte was read but no target came out. Residual: a writer that sends 0 bytes and holds the pipe open still costs 2.0 s and falls back to `$1`.
  - Alternatively, narrow the spec's "stdin read that fails" to the design's two rc≠0 cases and state that non-JSON input falls back to `$1`.
  - Whichever is chosen, add a fixture: non-JSON stdin plus `$1`.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `or a stdin read that fails, is no target`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `pipe held open with no data costs the 2.0 s bound and then falls back to `$1`.`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `stdin payload present but unusable (a control character in the target, or the reader failed)`
- (unverified) Existing and planned hook tests inherit the test runner's fd 0, and the new gate now reads fd 0.
  - The existing helpers do not pass `stdin=`: `test_h_mad_tdd_gate_state_resolution.py:65` and `test_h_mad_tdd_gate_codex.py:66,116`. Grok Task 12's harness, `subprocess.run(["bash", HOOK, "shared/widget.py"], cwd=project, env=cell_env)`, does not either.
  - If the runner's stdin is a pipe held open (a dispatcher or harness parent), each call costs 2.0 s. For grok's 177 items that is about 6 minutes. If that stdin carries bytes, the first gate call consumes them.
  - The design measured only two environments: explicit `/dev/null`, and the Bash tool (0.06 s). I could not check what fd 0 is under `codex exec`, `hmad-dispatch`, or the mutation harness.
  - Prescription: every test that invokes the Claude gate passes `stdin=subprocess.DEVNULL` or `input=<payload>`. AC-6.2's "no other assertion changes" allows this, because it is not an assertion. Name it in the AC-6.2 migration and in D13's grok re-plan list.
  class: build
- The D12 claim that pytest is importable "by construction" is false when the test runner is itself a venv interpreter.
  - What I ran: a venv built with `--without-pip`, then a second venv built from the first one's `bin/python` with `--system-site-packages`. The second venv's `pyvenv.cfg` read `home = /opt/anaconda3/bin`, and it could not import a module placed in the first venv's site-packages.
  - So `--system-site-packages` reaches the base interpreter's site-packages, not the runner's venv. The real-symlink rows would then read `pytest-missing`: AC-3.3 (accepted with the real `bin/python`) and the versioned-spelling rows.
  - It holds on this machine, where `python3.11` is `/opt/anaconda3/bin/python3.11` with `sys.prefix == sys.base_prefix`.
  - Prescription, either: state the precondition `sys.prefix == sys.base_prefix` and skip with a named reason otherwise; or build from `sys._base_executable` and assert `import pytest` in the built venv as a fixture precondition. The marker-shim rows are unaffected, because they `exec` the builder itself.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `by construction, because it is running the test.`
- The D13 "What grok's Task 12 must re-plan" list is incomplete. The class is every grok artifact anchored on pre-feature gate text, and the list names only WR12 among the mutation rows.
  - Task 14's `tdd_gate_fallback_agent.json` rows all anchor on text this feature deletes (impl-plan Task 14 table, read at the grok worktree):
    - G1 and G2 find `exit 1 ;;⏎  "invalid "*)`;
    - G3, G4 and G5 find `jq` filter text;
    - G6 finds the `*)` arm, whose role D13 hands to the ERE.
  - AC-2.7 ("carries G1–G3") goes with them.
  - Task 12's header also changes. It lists **Production file** `h-mad/hooks/h-mad-tdd-gate.sh` and a WIRE inside that file, but D13 item 1 puts the fold in `h_mad_tdd_judge.py`, so the Task gains a second production file and a judge-side wire.
  - Test 2 asserts that stderr names `fallback_agent=<json.dumps(value,…)>`. D13 item 4 decodes only the key and the state file; the `invalid:` payload must be `_pct_decode`d too.
  - grok spec AC-2.5 ("a different feature … that is not `ACTIVE`") means ACTIVE = `head -1`. Under D13 item 2, a second step5 record is ACTIVE and its `grok` blocks, so AC-2.5's wording needs routing to grok's spec.
  - Add all of these to the list, or state that the list is non-exhaustive and give the grep that enumerates it.
  class: build
- D13 leaves the fold field's name and grammar as "for example".
  - A re-plan needs one fixed spelling, because the D10 ERE is a closed whole-line grammar and grok's tests would pin it.
  - Either fix it here (`fallback-block=(none|grok:[1-9][0-9]*|invalid:[1-9][0-9]*)`, where it sits in the line, and the `B ≤ records` cross-check), or say explicitly that grok's design owns the spelling.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `(for example `fallback-block=none|grok:<B>|invalid:<B>`, with `B` the`
- An empty field value makes the `state` line fail the gate's own ERE.
  - `urllib.parse.quote("", safe="/._-")` returns `''` (executed). A record whose `codex_status` is `""`, or whose key is `""`, therefore prints an empty comma field.
  - Each `record=` subfield is `[^ ,]+`, so the line is a grammar miss. Every governed write is refused `judge-error` instead of the Codex-authorship refusal. That fails closed, but the refusal names the wrong cause.
  - The class is any variable field whose value can be empty. Rule: encode an empty value as a token `quote()` never emits, such as a bare `%` (not `-`, which `quote` leaves unencoded and so collides with a real value `-`), or have the judge map `""` to `available` for `codex_status` the way it maps `null`. Add one row per field to the D10 round-trip test.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `Every variable field value is `urllib.parse.quote(value, safe="/._-")``
- The open category axis turns ordinary untimed noise into summary lines, and the D7 residual does not name this.
  - I executed the D7 regex. `2 rows inserted` and `5 files would be left unchanged` both match as untimed summary lines. Any `N words in Xs` line matches as a timed one.
  - Because the parser reads `stdout + stderr`, a timed lowercase line on stderr now beats pytest's real stdout summary. The v1.0 closed word set would have rejected it.
  - Every consequence fails closed (0/0/0 → judge rule 8 or `no_summary`), but a RED run can be denied `no-tests-ran` for reasons unrelated to tests.
  - Either state this residual beside `3 apples`, or score only stdout lines for the timed-beats-untimed rule (pytest writes its summary to stdout).
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `It is a summary`
- Spec v1.4 still says `_resolve_state_file` is kept, while the design and plan delete it.
  - The spec says it keeps "its role of taking the fast no-op path", and its "Unchanged" bullet names "the `_resolve_state_file` fast path".
  - Design D9 step 4 replaces it with `_chain_may_hold_state`, lists it under "What leaves the gate", and adds a 5g grep `grep -c '_resolve_state_file'` → 0. Plan v1.3 layer 6 step 1 says "It replaces `_resolve_state_file`".
  - An implementer who follows the spec keeps a function the 5g grep then fails on. Sweep both spec sites, lines 555–556 and 573.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `keeps only its role of taking the fast no-op path`
- Plan v1.3's merge-condition list was not updated for the OQ-D1 host-deadline probe.
  - Spec v1.4 OQ-D1 and design D6, Implementation Order and Invariant Compliance all call the probe a merge condition.
  - The plan's §"Merge conditions" (lines 89–92) and its line 1416 still list only V-0 and V-1r.
  class: measurement
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `Both are merge conditions (R1;`
- Design v1.1 is stale at 037c9f6b in 10 sites, each saying a sibling revision "owes" text that plan v1.3 or spec v1.4 has since landed.
  - Seven are cells in the DD table's "Now" column: DD-1, DD-2, DD-3, DD-4, DD-6 and DD-10 owe the plan, and DD-11 owes the spec. All 7 were checked landed:
    - plan layer 6 reorder;
    - plan "What we deliberately do not touch" and Out-of-Scope;
    - plan "One predicate";
    - plan SGR bullet;
    - plan accounting sentence;
    - plan Time bound;
    - spec FR-4 rule 2.
  - Three are prose sites: D8's "a sentence in FR-5 is owed" (landed as spec v1.4 FR-5 "Unreadable before the filter"), D8 Differential's "accounting sentence is owed", and D11's "the report routes that to the spec" (spec v1.4 FR-7).
  - The Overview also still says "implements spec v1.3 … and plan v1.2".
  - Rewrite the column as "Adopted by …" and fix the Overview pointer. That is one population of 10 plus the Overview; do not re-count it separately.
  class: measurement
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `The design implements spec v1.3 FR-0…FR-8 and plan v1.2.`
- Spec v1.4 leaves DD-7 conditional although design v1.1 decided it.
  - Design DD-7 says "Kept (orchestrator OD-E …)", and plan v1.3's table says "AC-6.15 (DD-7, kept by design v1.1)".
  - Spec FR-6 "Relative target" and AC-6.15 still read "[conditional on design v1.1 keeping DD-7]", and the Decisions table has no OD-E row.
  - Resolve the condition and record OD-E (and OD-F / D13 if the spec is to know about it).
  class: measurement
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `[conditional on design v1.1 keeping DD-7]`
- Plan §"Stamps" was not swept for audit-gate change 2.
  - It still says the change "moves a new stamp from `UNREADABLE` to `FAIL`", as if that were the only move.
  - Spec v1.4 FR-4 change 2 also moves a coloured failing summary from PASS to FAIL. That is a new stamp moving from PASS to BLOCKED `suite_fail:`.
  - "No PASS flips" is true only in the sense "nothing flips toward PASS". Say that, and add the PASS→FAIL move.
  class: measurement
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `therefore moves a new stamp from `UNREADABLE` to `FAIL`, and an `EXIT:` reason from`

## Nit
- The rule-2 wording differs across the documents. Spec FR-4 rule 2 says "after SGR and whitespace stripping". Design D7 rule 2 says "after stripping", which by D7's grammar also strips `=` padding. The two differ on a line ending `pytest ====`. Pick one wording and use it in all three documents.
- The plan's summary-line rule says a category with "other punctuation" is not a summary line, and never says that `-` is allowed. Spec FR-4 and design D7 allow `-` explicitly ("punctuation other than `-`").
- Spec FR-1's ALLOW line still says `test=<repo-relative path>`. Design D10 now allows an absolute `test=` for a test outside the root.
- Plan R1's mitigation still says "AC-6.1–AC-6.4 may be implemented", citing spec v1.1. Spec v1.4 AC-6.7 now says AC-6.1–AC-6.4 and AC-6.8–AC-6.15.
- The D13 grok HEAD reading (`199eaf89`, Task 9 GREEN) has moved again. The HEAD is now `893c2b68`, Task 10 GREEN. `grep -c fallback_agent` still reads 0, and the gate's last commit is still `dde1c7ad`, so the conclusion stands.
- The AC-6.11b mutant note calls climb plus failed-`cd` "redundancy". Removing the climb alone preserves every verdict: it only defers a missing-parent write that the `state` verb then reads as none. So the climb is a precision step, not a safety guard, and it has no guard of its own to mutate. Say so rather than "back each other up".
