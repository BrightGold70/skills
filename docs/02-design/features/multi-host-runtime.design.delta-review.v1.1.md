## Summary
This is an advisory delta review of `b327e8bf..dffd0814` (design v1.0→v1.1, spec v1.2→v1.3). Neither file changed at HEAD `eec0c7a6`, and nothing under `h-mad/` or `handoff/` changed either. Every codex p1 must and teammate must is answered in text, and most repairs close the class, not only the instance. Several premises reproduce:
- both `--check-anchors` runs (`specs=99 mutations=907 drifted=0`, `specs=7 mutations=69 drifted=0`);
- the 16/3 spec-file census;
- AC-8.3's `31 passed` under both host values;
- DP5/F11 counts (9 `available_commands`, 316 distinct `str`, identical across all 9, 0 `system`, 0 non-JSON);
- DP6/DP14. A literal scratch build of the §D10 classifier reproduced all three predicted replay verdicts;
- codex `send_message` at 39 matching lines;
- `hmad-dispatch.sh:2503`;
- the `10-hooks.md` `permissionDecision` sentence;
- the sibling FR-0 branch tokens.

The new V-11.1 tokenizer does have a false-PASS path I executed: shlex's default `#` commenter swallows a script run. Spec v1.3 and design v1.1 also disagree on the V-11.1 verdict set, although they were committed together. And several fixtures that spec v1.3 newly names have no owning test in the design.
Evidence: 29 files opened, 41 greps run (plus executed: check-anchors ×2, pytest ×2, a scratch D10 classifier replayed over the 3 committed logs, 4 shlex probes).

## Must-fix
- **The D10 tokenizer as configured drops executions, which gives a false `PASS`.**
  - The mechanism: `shlex.shlex` defaults to `commenters="#"`, and the design never overrides it. I ran the exact configuration: `shlex.shlex(t, posix=True, punctuation_chars=";&|<>()\n")`, `whitespace=" \t\r"`, `whitespace_split=True`.
  - `echo start # note\npython3 h-mad/scripts/h_mad_state_write.py x` tokenizes to `['echo','start','python3','h-mad/scripts/h_mad_state_write.py','x']`. The comment consumes the newline separator, so the run becomes operands of a non-executing `echo`.
  - `echo ${#x}; python3 h-mad/scripts/h_mad_state_write.py s --feature f` tokenizes to `['echo','${']`. A mid-word `#` starts a comment, so the whole run vanishes.
  - In both cases, a script run before the adapter read is never seen, and a later adapter read then yields `PASS`.
  - With `commenters=""` the first input gives `[... '\n', 'python3', 'h_mad_x.py']`, which is correct.
  - Two more members of the same class (tokenizer config vs shell grammar):
    - Redirects: `cat a >> b` yields a `>>` token. The design drops the target only after "A `<` or `>` token", so `>>` keeps `b` as an operand. `cat x >> …/grok-runtime.md` then counts as a content **read** of the adapter.
    - Heredocs: an English apostrophe in a heredoc body raises `ValueError: No closing quotation`. That gives `UNVERIFIED … unparseable command` anywhere in the log, because step 4 scans every position. This one is conservative.
  - Rule over the class: every shell metacharacter that `bash`/`zsh` treat specially is either modelled or makes the simple command unclassified. The residual is stated per member.
  - Repairs, any combination:
    - (a) set `commenters = ""`. Comment words then become operands, and a mentioning comment in an unclassified command halts, which is conservative;
    - (b) or strip `#` comments with a quote-aware scan that keeps the newline;
    - (c) treat any token made only of `<`, `>`, `&` and digits (`>>`, `<<`, `>|`, `&>`, `2>`) as a redirect that drops its target;
    - (d) state the heredoc/apostrophe halt as a residual.
  - Add rehearsal cases `echo x # c⏎<run>` → `FAIL`, `echo ${#x}; <run>` → `FAIL`, and `cat y >> <adapter>; <run>` → `FAIL`.
  instance of: tokenizer configuration vs shell grammar
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `Each command text is split into **simple commands** with`
- **Spec v1.3 and design v1.1, committed together, disagree on the V-11.1 verdict set.** A Phase-6 rehearsal expectation therefore differs depending on which document the implementer follows.
  - For codex/agy with no `SKILL.md` read, the spec says `FAIL`. The design's step 4 says `UNVERIFIED V-11.1 no observed SKILL.md read` "(every host)", and R11 expects `UNVERIFIED` for each host.
  - The spec limits `UNVERIFIED` to "grok skill load only". The design emits it for:
    - an unparseable line;
    - an unobserved input shape;
    - an unparseable command;
    - an unclassified mentioning command;
    - a missing `SKILL.md` read on every host.
  - The spec says the verdict "is exactly one of" three. The design has a fourth, `UNREADABLE V-11.1 reason=<r>` with exit 2.
  - The design's §"Spec restatements this design depends on" list names none of these, so the checklist it offers for the spec revision cannot detect the gap.
  - Repair: restate the spec's V-11.1 verdict paragraph and its codex/agy skill-load clause to the design's four tokens and every-host `UNVERIFIED`, and add that sentence to the restatement list. Or change design step 4 and R11 to `FAIL` for codex/agy.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `For codex and agy: an observed successful content read of h-mad's`
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `The verdict is exactly one of`
  quote: docs/02-design/features/multi-host-runtime.design.md › `There must be a successful content read of`
  quote: docs/02-design/features/multi-host-runtime.design.md › `prints exactly one line, and it is one of four`
- **Fixtures that spec v1.3 adds to its ACs have no owning test in the design's Test Strategy inventory.** The design's §Test Strategy list is what Phase 5 turns into RED tests, so the RED/GREEN set is short.
  - AC-10.3 now requires, one fixture each: `HMAD_AGENTS_SKILLS_DIR=""` with no option → `UNREADABLE`, and the same for `HMAD_AGY_SKILLS_DIR=""`. It also requires an explicit option that beats an override pointing elsewhere, one fixture per option.
  - The design's `test_h_mad_install_check_roots.py` list has only `test_empty_root_option_is_unreadable[agents|agy]` (the option form) and a single `test_env_override_is_read`. D6 lines 584–588 do describe the behaviour.
  - AC-9.1 now requires the live-foreign-owner/no-owner **pair** for `HMAD_HOST=zzz`, and the same pair for `HMAD_HOST=grok --session-id ""`. The design has a singular `test_decide_unknown_host_without_session_id`, and no empty-id case in `test_decide_cannot_judge_without_session_id[<host> × …]`. D5 states the empty-id rule, but no test lists it.
  - Repair: add `test_empty_env_override_is_unreadable[agents|agy]` and `test_explicit_option_beats_env_override[agents|agy]`. Parametrize the unknown-host and empty-id cases over `<live-foreign-owner|no-owner>`. Names are proposals.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `The same holds, one fixture each, with no option passed and`
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `gets the same pair, and so does`
  quote: docs/02-design/features/multi-host-runtime.design.md › `test_decide_unknown_host_without_session_id`

## Should-fix
- **The fenced lines D12 pins may be invisible to `_fence_events`.**
  - D12 pins "fenced lines" among the `body` events of `_fence_events`. The design's own D9.3 model nests each ```` ```bash ```` fence 4 spaces deep under a list bullet.
  - `_fence_events`' opener is `^(?P<indent> {0,3})…` (`h-mad/scripts/h_mad_doc_block_exec.py`, in `_fence_events`). An adapter that mirrors the design's layout therefore yields `prose` events. The AC-9.3 pins and the FR-8 "exactly one fenced line matching `^HMAD_HOST=…`" test then find 0 lines. The failure is loud, not a false pass.
  - Repair: state that the adapter fences open at indent 0–3 (outside list items), or strip leading indent before matching and recognise nested fences.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `Every command shape below sits in a fenced`
- **The minted-id fence gives `--claim "$SID"` with no `--create`, which fails for a new feature.**
  - `h-mad/SKILL.md` (the claim block after the resume-oracle command) states that "`--claim` ALONE exits 2 here with `ERROR: no such feature`" on `start_fresh`, and that `--create --claim` is required there.
  - An orchestrator on codex/agy/grok that follows the adapter's runnable line for a new feature exits 2.
  - Repair: add the `--create --claim "$SID"` line for `start_fresh`. The AC-9.3 pin on `--claim "$SID"` still matches it.
  - Also list the `h_mad_resume_decision.py` line first, because the oracle decides before the claim. That is a nit.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `takes the id as its value, and`
- **The "sed is the one unclosed member" residual is false.** `rg --pre=COMMAND` ("Search output of COMMAND for each PATH", ripgrep 15.2.0 `rg -h`) executes a command, and `rg` is in the non-executing set.
  - Rule over the class: any option of a "non-executing" command that runs a program. Today that is `sed` `e`/`--expression` and `rg --pre`/`-z`.
  - Repair: either `rg` with any `--pre*`/`-z` option is unclassified, or list the residual.
  instance of: non-executing set membership
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `is classed as non-executing even though GNU`
- **OD-a and OD-b are referenced three times (design §D10 Residuals, grok R1, §Test Strategy) and defined in no committed feature document.** `grep -rn 'OD-b\|OD-a'` over `docs/01-plan/features/multi-host-runtime.*` and `docs/02-design/features/multi-host-runtime.*` finds only those 3 lines.
  - OD-b is load-bearing. The design predicts that grok's `UNVERIFIED` step 4 "may be the usual outcome", and it routes `UNVERIFIED` through `recover`, which reverts.
  - That recreates the harm §Supersedes item 1 was written to remove: "every grok smoke prints `FAIL V-11.1`, and `recover` then reverts a good integration".
  - Repair: record OD-a and OD-b, with their options, in the design or in a committed decisions section.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `it is the orchestrator's decision (OD-b)`
- **The live-smoke record path changes the plan's resolution without a §Supersedes entry.**
  - The plan writes the record into the archive directory 7c created (plan Deliverables row; plan smoke part 2, "the directory 7c created").
  - v1.1 moves it to `docs/03-analysis/multi-host-runtime.live-smoke.md` and declares archiving "not settled". That reopens a gap the plan had closed.
  - The Overview still claims every other plan decision is kept.
  - Repair: add a §Supersedes item with its revert, or keep the plan's path and note that the spec's FR-11 path is owed a restatement.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `The smoke writes the record at`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `written after 7f into the directory 7c created`
- **Spec v1.3 says every failure line carries a `reason=`. The design makes it optional.**
  - The design declares `Failure.reason: str | None = None` and the grammar `[reason=<r>]`. `UNREGISTERED file=<SKILL.md> id=- token=<hit text>` has none.
  - A test written from the spec asserts a field that single-disjunct kinds do not print.
  - Repair: make the spec say "a kind with more than one disjunct carries `reason=`, and the pair is `(kind, None)` otherwise", or print a reason for every kind.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `Each failure line also carries a`
  quote: docs/02-design/features/multi-host-runtime.design.md › `reason: str | None = None`
- **D12 pins `exit 2` for refusal form (a), but D9.2's prescribed row-(a) wording contains no `exit 2`. Neither does the spec's.** Both say "rc 2". An adapter that copies the prescribed wording fails its own doc test.
  - The other two rows carry their tokens: `exit 1` and `permissionDecision`.
  - This is the class v1.1 repaired for `fail-open`/`fails open`, re-opened on a new row.
  - Repair: write "rc 2 (`exit 2`)" in both documents, or pin `rc 2`.
  instance of: pinned token absent from prescribed wording
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `none: rc 2 is grok's documented`
- **Implementation Order step 1 is still unperformed.** `docs/03-analysis/probes/multi-host-runtime/` does not exist at `dffd0814` or at HEAD `eec0c7a6` (`ls` → "No such file or directory"). v1.1 re-scopes the step to "before the design gate clears", so this cycle cannot clear the gate under the design's own order until `calibrate.sh`, `seed.json` and `seed_coverage.py` are committed.
  class: measurement
  quote: docs/02-design/features/multi-host-runtime.design.md › `Before the design gate clears`
- **The design still describes the superseded spec text.**
  - The Overview says the design "implements spec v1.2", but spec v1.3 landed in the same commit.
  - §Supersedes item 1 says spec F11 expects a `system`/`init` line. Spec v1.3's F11 now says the opposite.
  - Items 1, 2 and 5 (and AC-4.2 and AC-5.2) are now spec text, not divergences.
  - Repair: re-point the Overview to v1.3, and mark adopted items "adopted by spec v1.3".
  class: measurement
  quote: docs/02-design/features/multi-host-runtime.design.md › `The design implements spec v1.2 (FR-1 to FR-12)`
  quote: docs/02-design/features/multi-host-runtime.design.md › `and spec F11, expect a`
- **The codex event rule reads codex's undelimited tool output as events.**
  - The rule is "each line equal to `exec`". In the text log, output lines follow ` succeeded in` with no terminator (`codex-text-8-exec.log`, e.g. lines 18–20).
  - An output line that is exactly `exec` (a `sed`/`cat` of a codex log, or of this fixture) therefore becomes an event, and the following line becomes a "command". That breaks the design's "input, never output" rule (§Supersedes item 2), and no residual states it.
  - I did not measure how often codex output contains such a line (unverified frequency).
  - Repair: state the residual, or bound an event to the text between two `exec` lines and a known codex section header.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `each line equal to`
- **unverified: in NDJSON logs, a non-beat, non-JSON line halts as `UNVERIFIED`, and the smoke's `recover` reverts.**
  - `hmad-dispatch.sh` itself states that its log "legitimately carries: pre-existing caller content, and our own `#hmad-beat` lines" (comment above `_agy_ndjson_response`).
  - The `exec grok` path does not exist in this tree (it is from the sibling feature, unmerged). I could not check whether grok stderr or dispatch text reaches `--log`.
  - If it does, every grok smoke halts and reverts. State the assumption: a fresh `$S/log` holds only host NDJSON and beats. Pin it at the first live smoke.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `any other line that is not a JSON object prints`

## Nit
- The restatement "F11 and V-11.1, grok" says the load "is shown by a completed `read_file` tool call". D10 also accepts a shell content read for grok, and the spec says "by the same predicate", so the restatement is narrower than both.
- The spec FR-8 residual says the `HMAD_CONTEXT_WINDOW` `ValueError` is raised "before any statement of `main` runs". It is raised inside `main`: `h_mad_context_budget.py:141`, the `default=int(os.environ.get(...))` in `add_argument`.
- Rehearsal fixtures are "committed under `rehearsal/`", yet "if the `grep` returns nothing, the fixtures are unbuildable and the rehearsal prints `FAIL`". It is unclear whether `rehearse` regenerates the grok fixtures from the sibling log at run time or reads committed copies.
- The content-read set is closed (`cat head tail nl sed`). `less`, `awk`, `bat` or `python3 -c "open(...)"` reads of the adapter give `FAIL no adapter read`. That is conservative, but the residual lists only the glob and relative-path cases.
- In the execution rule "`argv0` is `bash`… and the first operand…", it is unclear whether options such as `-x` are skipped before the first operand is taken.
