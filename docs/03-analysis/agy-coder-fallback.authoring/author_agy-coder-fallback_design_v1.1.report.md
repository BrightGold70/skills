DESIGN-AUTHOR: DONE version=v1.1 path=/Users/kimhawk/orca/skills/docs/02-design/features/agy-coder-fallback.design.md lines=1143 sha256=9f2d8acefee842c645d0331d473354ccd310bbaf0d8190ae53f7702c9c31a46d

# Design v1.1 report: agy-coder-fallback

Start state: v1.0 at df46f72a, sha b7057f78…, newest VH v1.0. Re-checked before the writes and unchanged; the only writer was me. Spec v1.7 (c117a695, 390c4771…) was read once the coordinator's mid-task message arrived. The plan in the working tree is modified and uncommitted (plan-author is working on it). I did not read it.

## Applied, per item
- **C1.** Leap second: the design now cites spec FR-1/D-14 (seconds 00–59) and no longer calls it a residual. I removed it from §Residuals. Added fixtures: 23:59:60Z refused, 23:59:59Z accepted. The AC-1.2 row now reads 5 refused values and 2 accepted.
- **C2 + C3 (closed as a class).** FR-4 class (b) is now the Codex gate's per-target sequence, T1–T7, taken from `_relative_target` plus the body of the `# M:G5` loop:
  - T1 expanduser canonicalise; T2 unresolvable; T3 containment check before `_is_shell_allowance`; T4 outside the root; T5 allowance file; T6 production checked over every `names` entry, then `min`; T7 read_chain with its unreadable / not-active branches.
  - The audit missed one more member, which I added: v1.0's step 4 "inactive allows" before class (b) is exactly row G5's mutant. Activity is now an input to each class, never a global shortcut.
  - The deliberate differences from the Codex gate are listed (4 items).
  - The AC-4.1 row gains a target differential test: target corpus × status, both gates.
  - Also from the class: the no-path-key deny now applies only when the status is active or unknown, as the Codex gate's no-target deny does.
- **C4 / C11.** I defined the WIRED fixture in FR-5. In the AC-9.1 row the loop gets agy, the fixture is set up once before the loop, `run_cli` gets an env override, and the assertion becomes `len(set(hashes))==1` over 3 hashes.
- **C5.** Dropped the in-place-append row and said why. Replaced it with a `[]`-base loss mutant, an accumulation-from-prior mutant, and a mutant that removes the same-key refusal.
- **C6.** Follows spec FR-7 §Attribution:
  - A module's authors are the `--agent` values of its accepted implementation dispatches.
  - A 5e entry follows the any-author rule.
  - 6a-prime writes one entry per module, with authors read back from the 5e entries.
  - Same class, also fixed: the `unrecorded` detail text no longer reads `implementer_switch.to` or `implementer`. It gets a switch/recovery fixture and a mutation row.
- **C7.** Appends accumulate from the updated record, in command-line order. `--set` and `--append` naming the same key in one call is refused with exit 2.
- **C8.** The guarded-import failure is re-raised as the first statement of `_main_guarded`, so `# M:G2` converts it and row G2 stays killed. Rule over the axis: no new early return before the G2 `try`.
  - `--self-check` prints `FAIL policy-import` and exits 2.
  - Removing the re-raise is declared an equivalent mutant (no row). Reason: every allow path calls `_any_phase5_status` first, so the outcome is a deny either way.
- **C9.** Class (c) computes `cwd` the way `_command_cwd` does, with the root standing in for the session cwd:
  - Malformed → MALFORMED_WORKDIR; absent / None / "" → root; a relative path is joined to the root.
  - The gate runs `chdir` only into an existing command directory and otherwise stays in the root. A bad Cwd never gives judge-error.
  - The fixtures mirror the Codex workdir tests.
  - I did not take the reviewer's "always chdir(root)": a relative script would then be judged at `root/<tok>` while the shell runs `<cwd>/<tok>`.
- **C10.** `_semantic_ok` never raises, and `classify` keeps its existing isinstance-first line. The four new properties go after `fallback_agent`, and the rule over the axis is stated.
- **M1.** Two committed probes, both `PROBE: PASS` at 200ffd52:
  - `docs/03-analysis/probes/agy-coder-fallback/fr3_state_line_grammar.py`. It derives the grammar from the hook literal. A control copy that expects the today-shape line to match prints FAIL.
  - `docs/03-analysis/probes/agy-coder-fallback/fr6_import_failure_pair.py`. It runs 4 tree variants, including the G2 mutant, which proves G2 is reached through the identity import failure.
- **OQ-A / OQ-B** are now §"Operator decisions", citing D-12 and D-13.

## Premises verified (command → result)
- `git diff --stat 29ae3e7b 200ffd52 -- h-mad | wc -l` → 0, and the same against the working tree → 0.
- Read the Codex gate's `_main_guarded`, `_relative_target`, `_is_shell_allowance` and `_command_cwd` with `sed -n` on `h-mad/hooks/h-mad-codex-tdd-gate.py`.
- Mutation rows G2 and G5: parsed with python over `h-mad/tests/mutation-specs/*.json` (found in `codex_gate_judge_wiring.json`).
- The `test_codex_gate_kind[judge-error]` tree has no identity module (sed).
- Scratch python call via runpy (deleted afterwards):
  - hard link `names=('test_a.py','z.py')`: checking the target alone → False, checking any name → True;
  - `_is_shell_allowance` on an outside path → ValueError;
  - `Path('').resolve()==cwd` → True;
  - `_safe_shell_command('ls', …)` with MALFORMED, a nonexistent dir and "" → True, True, True.
- `test_prompt_file_is_agent_independent` loops over ("codex","grok") and checks `hashes[0]==hashes[1]` (grep -A).
- Schema property order ends `codex_status, fallback_agent` (python json). The `index(...)+1` assert is in test_h_mad_state_fallback_agent.py. `classify` starts with the isinstance guard (sed). CORPUS has `["nope"]`.
- `_mutate` holds the flock around apply and write (sed). `merge_fields` is `{**prior, **fields}`.
- Spec AC-4.1: "With step5 inactive, the agy gate allows every tool." T7 is consistent with this because the chain, not rglob, decides "inactive".
- Precheck: `[H-MAD] precheck … PASS issues=0`. 19 PATH advisories, all new files or fixture paths (`h-mad-agy-tdd-gate.py`, `.agents/hooks.json`, `src/test_a.py`, `src/z.py`, `docs/x.py`, new tests and specs). All kept on purpose.
- VH: `VERSION-HISTORY: OK … version=v1.1`.

## Sweeps
- grep -c for retired phrasings → 0 each: "allowance file denies, through", "canonicalise(str(root), raw", "changes its own working directory", "Open questions".
- Collapsed-newline grep for "implementer_switch.to`, else" → 0.
- The `leap` entry was removed from §Residuals. The 25 / 31 counts are unchanged, because no moved name was added (T3 reorders calls; the helper stays byte for byte).

## Owed by other documents
- **Plan:** M-4 is 31 rows, not 19; DO-2's version condition; D-12/D-13 mirrored. All in progress by plan-author.
- **Spec (advisory):** FR-4 says "same rules as the Codex gate". The design lists 4 deliberate differences (§FR-4) that the spec could adopt.
- **Spec (advisory):** FR-7 "names that agent" does not say which author is named when the reviewer is not among the authors. The design names the author of the latest successful dispatch.
- **Impl-plan:** committed probes for the M-3/M-4 censuses, the inventory, the FR-9 corpus and the replay.

## Notes
- The FR-1 predicate's own scratch probe (v1.0) is still described as deleted. M1 named only FR-3 and FR-6.
- I removed my own scratchpad files. A `mrows.py` in the session scratchpad is not mine; I left it.
