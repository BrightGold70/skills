# R21 scoped review @95ccfd12 (relayed by SendMessage, chunked)

## chunk 1/2 — R21-F1 HIGH fail-open PASS, single event
Clause (a): same-event rule + "canonical() no longer checks the script name". The removed name check is still needed because classify() and canonical() disagree on which word is the script. classify()'s python branch first loops over ALL args (the -m loop) — any later `-m h_mad_x` / `-mh_mad_x` / `-m pkg.h_mad_x`, even AFTER the script operand, returns kind=script. python3 runs the first operand; the rest is the script's argv. So `HMAD_HOST=agy python3 h-mad/scripts/h_mad_derive_test_path.sh -m h_mad_state_write`: fits CANONICAL; canonical() → 'agy' (.sh exists, name unchecked); classify() → declaring script in SAME event → canonical_ok True; mention 1 vs 1 → PASS with no h_mad_*.py run anywhere.
Fixture (agy): R19-ctrl steps 1-2 (view_file SKILL.md, agy-runtime.md ACTIVE+DONE), then step 3 run_command ACTIVE + DONE (output "") CommandLine "HMAD_HOST=agy python3 h-mad/scripts/h_mad_derive_test_path.sh -m h_mad_state_write".
Observed PASS V-11.1 on 3.14.7 and 3.11. Expected UNVERIFIED not canonical.
Variants all PASS both interps: A2 h_mad_state_schema.json -mh_mad_x; A3 hmad-dispatch.sh -m x.h_mad_y; A4 h_mad_emit_marker.sh --flag -m h_mad_z; G1 grok (R20-F1-grok rows 1-5 + t4 {"command":"HMAD_HOST=grok python3 h-mad/scripts/h_mad_derive_test_path.sh -m h_mad_state_write","description":"x"} completed); M1 = A1 + never-DONE bash -c declaration.
Controls: A1-ctrl-sh (no -m) → UNVERIFIED HMAD_HOST used outside an exact declaration; G1-ctrl same; A1-ctrl-py (h_mad_state_write.py -m h_mad_state_write) → PASS correct; M2 (A1 no reads) → FAIL no adapter read (event classified as script).
Live zsh+bash, stub root with h_mad_state_write.py (+ copy in cwd so -m would resolve): .sh -m … → "SyntaxError: invalid syntax", rc=1, no RAN; control .py → "RAN … agy" rc=0. agy success = DONE exists (trusted) so rc=1 counts as completed.
Why R20 fuzz missed: its -m special never followed by an h_mad_ module name; before 95ccfd12 canonical event did not have to be classify-declaring.
Fix (both): (1) canonical() require SCRIPT.fullmatch(name) again, correct comment — classify() is not equivalent. (2) classify() python branch: honour -m only while scanning options BEFORE first operand (merge into ordered operand loop). Pin A1, A2, G1, A1-ctrl-py.

## chunk 2/2 — coverage, no finding beyond R21-F1
Baseline rehearse PASS n=271 on 3.14.7 and 3.11.
- Regex vs shlex: WORD has no quote/glob/~/{/=-first/separator → shlex.split == space-split; only disagreement is classify -m scan (F1). A path WORD starting with `-` cannot bind under root/h-mad/scripts.
- shlex fallback: canonical text cannot raise (no quotes) → declares=False only on non-canonical (conservative).
- C1 canonical HMAD_HOST=grok in agy log + agy bash -c → FAIL another HMAD_HOST (correct).
- C2 canonical .py never DONE + canonical .sh DONE → UNVERIFIED (correct).
- C3 agy params {CommandLine, Cwd} → UNVERIFIED shape (correct).
- C4 canonical .sh + bash -c with two inner scripts (1 mention → 2 declarations) → UNVERIFIED not canonical (same-event rule holds).
- C5 genuine canonical .py DONE + never-DONE `HMAD_HOST=agy bash -c "a.py; b.py"` + `echo HMAD_HOST` → PASS (valid canonical exists; not fail-open). Note (R20 secondary, not filed): bash -c double count still lets a non-declaration mention balance the count, contradicting the comment.
- grok failed never sets success; rawInput-on-update, duplicate terminal, reused id, update-before-call → ShapeError.
- agy reused index w/ different params → ShapeError (identity incl. DONE); identical reuse deduped; DONE before ACTIVE → ShapeError.
- (b) keys: agy == {CommandLine}; grok ⊆ {command, description}; empty dict → None value → ShapeError. Both live logs still PASS.
Fixtures: 15 logs in scratchpad r21 (A1-sh-dashm, A1-ctrl-sh, A1-ctrl-py, A2-json-dashm, A3-dispatch-dashm, A4-emit-dashm, G1-grok-sh-dashm, G1-ctrl, M1-dashm-plus-bashc, M2-dashm-before-reads, C1–C5), gen.py, live/. No tracked edits.
