# R20 scoped review @0ce01a20 (relayed by SendMessage, chunked)

## chunk 1/4 — 1 HIGH (F1), 1 MED (F2), 2 LOW drift
Scratch S=scratchpad/r20. Baseline rehearse PASS n=256 on 3.14.7 and 3.11.

F1 HIGH fail-open PASS. Clause (a)+(b): spec says <script> lexically <root>/h-mad/scripts/h_mad_*.py; canonical() never applies SCRIPT — accepts ANY existing file in h-mad/scripts (h_mad_derive_test_path.sh, h_mad_emit_marker.sh, hmad-dispatch.sh, h_mad_state_schema.json, h_mad_state_schema_historical.json). The comment "h_mad_*.py name already required by classify(), which supplies declared" is a false premise: declared and canonical_hosts are filled from DIFFERENT events. Non-.py canonical event is classify-unknown → its HMAD_HOST counts as mention not exact declaration; mention gate is balanced by a 2nd defect: `HMAD_HOST=x bash -c "A; B"` gives the outer assignment to BOTH inner commands → ONE textual mention adds TWO exact_declarations.
Fixture S/F1-sh.log (agy): R19-ctrl's two view_file steps, then
 step 3 run_command ACTIVE ONLY (never DONE): HMAD_HOST=agy bash -c "python3 h-mad/scripts/h_mad_state_write.py --status; python3 h-mad/scripts/h_mad_state_write.py --status"
 step 4 run_command ACTIVE+DONE: HMAD_HOST=agy python3 h-mad/scripts/h_mad_derive_test_path.sh
Observed PASS V-11.1 on 3.14 and 3.11. Same for F1-json.log (h_mad_state_schema.json).
Grok F1-grok.log: t3 same bash -c status failed; t4 `HMAD_HOST=grok python3 h-mad/scripts/h_mad_derive_test_path.sh` completed → PASS both.
Link L3-link-sh.log: step 4 `HMAD_HOST=agy python3 S/lnk/scripts/h_mad_emit_marker.sh` --link S/lnk → PASS.
Expected all: UNVERIFIED (declaration not in the canonical form).

## chunk 2/4 — F1 evidence/controls/fix, F2
F1 live (zsh -c + bash -c, REAL checkout and stub root): h_mad_derive_test_path.sh → SyntaxError unmatched ')', no RAN; hmad-dispatch.sh → SyntaxError; .json → NameError 'null' (python3 EXECUTES a JSON file as a dict literal; a JSON file w/o null/true/false would exit 0 silently); link .sh → SyntaxError. Positive control both shells: canonical h_mad_state_write.py vs stub → "RAN agy".
Scorer controls: F1-ctrl-missing (h_mad_nope.sh) → UNVERIFIED not canonical; F1-ctrl-Aonly (step 3 alone) → UNVERIFIED HMAD_HOST used outside an exact declaration (double-count only matters once non-.py canonical mention is added). Fuzz with .py only: 0 fail-opens.
Fix: (1) canonical(): return None unless SCRIPT.fullmatch(name). (2) defence in depth: count an outer prefix assignment once not per inner bash -c command, or set declared only from canonical events. Add rehearsal F1-sh, F1-json, F1-grok, L3-link-sh → UNVERIFIED.

F2 MED (conditional fail-open). Relative <script> bound against <root>, shell resolves against the call's cwd. agy_events reads only CommandLine from run_command params; grok only rawInput.command; other keys (a per-call working dir) silently ignored (view_file path keys ARE shape-checked).
Fixture F2-agy-cwd.log: R19-ctrl rows 1-4, step 3 run_command params {"CommandLine":"HMAD_HOST=agy python3 h-mad/scripts/h_mad_state_write.py --status","Cwd":"/nonexistent"}, DONE output "python3: can't open file" → PASS. Grok twin F2-grok-cwd.log (rawInput.cwd=/nonexistent) → PASS. Live: cd /nonexistent; … → can't open file both shells. Control F2-agy-cwd-ctrl (no Cwd) PASS. Caveat: no live log shows per-call cwd (live agy cwd only on init row; live grok rawInput = command + description) → MED.
Fix: ShapeError when run_command params / grok rawInput carry keys outside observed set (agy {CommandLine}; grok {command, description}), or refuse canonical for relative scripts when such a key present.

## chunk 3/4 — drift
D1 LOW (drift, clause b). Spec: "A script call that declares this host in any other form gives UNVERIFIED … not in the canonical form." Code only checks `declared and host not in canonical_hosts` → non-canonical declaration forgiven whenever ANY canonical event for host completed.
D3-mixed.log: R19-ctrl rows 1-4, step 3 DONE `HMAD_HOST=agy python3 -V h-mad/scripts/h_mad_state_write.py`, step 4 DONE canonical → PASS; expected per spec UNVERIFIED. Control D3-ctrl (step 3 alone) → UNVERIFIED not canonical. Not fail-open (step 4 ran). Fix: reword spec, or make code UNVERIFIED on any non-canonical declaring script (also closes F1 alone). B1 inverse (completed non-canonical + canonical never completed) → UNVERIFIED, correct.
D2 LOW (drift, clause c). Spec parsing paragraph does not describe the shlex-ValueError fallback. Verified: C1 `echo done # it's fine` after reads → PASS; C2 `echo hi # don't run h_mad_state_write.py` before adapter read → UNVERIFIED unclassified command before adapter read; C3 `bash -c "echo it's"` (nested ValueError) caught → PASS. Fix: one spec sentence. Side note: outer `except ValueError -> unparseable command` now looks unreachable for shlex (not proven for other ValueError sources).
LOW residual wording: residual names environment and python3 resolution, not the shell's working directory (prior `cd` makes relative canonical script resolve elsewhere). Ties to F2.

## chunk 4/4 — coverage (no tracked edits)
(a) WORD/template fuzz LIVE zsh+bash vs stub root (shebang stub prints RAN+HMAD_HOST): 11 script forms (relative, ./, absolute, //, /./, trailing /, .//, leading-// abs, scripts/./, .sh, .json); arg specials x=y a:b +x - -- . .. // = -c -m -V --help a,b + =x x= -: -I -E -S -X -W : , ./ / + 300 random WORD args/seed. 608 texts × 3 seeds; canonical accepted 459/447/450; 104 fail-opens/seed ALL from .sh/.json (F1); 0 for any .py form. Trailing-slash → canonical None. python3 never reads args after script as options.
--link: L1 abs link + --link → PASS (live RAN agy); without → UNVERIFIED. `~` not in WORD → UNVERIFIED.
(b) D3-mixed (D1), B1 inverse correct, F1 double count; other_host + mention count via controls. grok failed never sets canonical_hosts (F1-grok-ctrl UNVERIFIED). agy success = DONE exists (F2: DONE with "can't open" still counts; trusted).
(c) C1/C2/C3. (d) depth: grok rawOutput n=198/199 PASS; 200/995/1200 UNVERIFIED unparseable line 5; identical 3.14/3.11; live max depth grok 6, agy 4. (e) strings() = old recursive on 20000 random structures, 0 mismatch. (f) not attacked. Live: grok-live PASS, live-agy FAIL no adapter read.
Fixtures (23 logs under scratchpad r20): F1-sh, F1-json, F1-ctrl-missing, F1-ctrl-Aonly, F1-grok, F1-grok-ctrl, F2-agy-cwd, F2-agy-cwd-ctrl, F2-grok-cwd, D3-mixed, D3-ctrl, B1-noncanon-done-canon-notdone, C1-apos-after, C2-apos-before, C3-apos-bashc, L1-link, L2-tilde, L3-link-sh, D-grok-{198,199,200,995,1200}; plus stub/, lnk, lnkstub, fuzz.py, de.py.
