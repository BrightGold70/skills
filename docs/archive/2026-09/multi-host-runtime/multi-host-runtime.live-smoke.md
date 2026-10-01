# Live smoke: multi-host-runtime (FR-11, V-11.1–V-11.5)

**Date:** 2026-10-01
**HEAD:** `58344684` (main; mhr merged and pushed 2026-09-29)
**Operator approval:** 2026-10-01, post-merge variant, all three hosts.

## Why a post-merge variant

The plan's smoke script (plan §"The smoke script") was written as a pre-push gate. Its part 1
halts on `integration already pushed`, and its `recover()` reverts every commit in `PRE..HEAD`.
After the merge and push, part 1 cannot pass, and running `recover()` would revert `main`.

The variant keeps part 2 as written: the pinned prompt, the `hmad-dispatch exec` call, and the
V-11.3/V-11.2/V-11.1 assertions in the same order. It also keeps part 1's host checks: the loader
symlink resolves to this `h-mad`, the adapter exists, and the prompt does not name the adapter.
It drops the pre-merge preconditions and `recover()`, so a failure reverts nothing.

The script was run from the session scratchpad and not committed. It is `smoke_postmerge.sh`
(plan part 2 with those removals).

## Results

| Host | Version | rc | Elapsed | V-11.3 tree + state sha | V-11.2 status | V-11.1 adapter read | V-11.4 session id | V-11.5 cost |
|---|---|---|---|---|---|---|---|---|
| codex | codex-cli 0.159.0 | 0 | 77 s | PASS | PASS | **UNVERIFIED**: codex input shape unobserved | `CODEX_THREAD_ID` set | 102,937 tokens |
| agy | 1.2.14 | 0 | 436 s | PASS | PASS | **FAIL**: no adapter read | `ANTIGRAVITY_CONVERSATION_ID` set | not reported |
| grok | 1.0.41 (4220f3b224a6) | 0 | 232 s | PASS | PASS | PASS | `GROK_SESSION_ID` set | 1,538 in / 1,913 out (93,952 cache read) |

All three hosts ended with the required line, which matches the state record:
`HMAD-STATUS feature=multi-host-runtime last_completed_phase=7 halt_reason=null`.

The tree was clean before and after every run. **None of the three changed the tree or the
state file**, so V-11.3 passed on every host.

## Reading the two non-passes

- **codex V-11.1 UNVERIFIED.** This is the residual the design documents. The codex log does
  not record which inputs codex read, so `smoke_assert.py v111` returns UNVERIFIED rather than
  PASS or FAIL. The mhr report records that a codex fix which invented a log format for this
  was discarded, and the residual was pinned instead. Unchanged.
- **agy V-11.1 FAIL `no adapter read`.** This is the verdict the mhr rehearsal predicted: see the
  mhr report §"The replay-agy rehearsal verdict", rated CHANGED/LOW. The live output shows why.
  agy answered by reading `docs/.bkit-memory.json` directly and never loaded
  `h-mad/references/agy-runtime.md`. The status it reported was still correct, and it made no
  writes. The open question is whether agy should be required to load its adapter for a
  read-only status call. It is a design question, not a regression.

## Verdict

FR-11 is exercised live on all three hosts:

- 3 of 3 are read-only: V-11.3 passed everywhere.
- 3 of 3 report the status correctly: V-11.2 passed everywhere.
- 3 of 3 report their session-id variable: V-11.4.
- Cost is reported where the host provides it: V-11.5.
- V-11.1 (adapter read) passed on grok only. It is unverifiable on codex by design, and it fails
  on agy exactly as the rehearsal predicted.

## Addendum 2026-10-01: operator decision on agy V-11.1

**Decision: lazy.** The adapter is required before any bootstrap, script, `hmad-dispatch` call or
write. A read-only `/h-mad status` on agy or grok may skip it when it reads files only through the
host's file-read tool and runs no shell command. A pure status read uses nothing the adapter
carries: its paths, hooks, claims and the install-check quirk.

Changes:

- `smoke_assert.py` `v111` issues the distinct token `PASS V-11.1 lazy (no script ran)`. It does so
  only when every event is a file-read tool call (agy `view_file`, grok `read_file`) or a non-acting
  agy step (`agent_response`, `user_input`, `checkpoint`), and when a `SKILL.md` read is observed.
  - Any shell command, unmapped tool, unknown step type or orphan grok update (of any status),
    without the adapter read, gives `FAIL … no adapter read`.
  - An agy tool step with no index, or a reused index, gives `UNVERIFIED`.
  - Codex cannot qualify, because every codex event is a shell exec.
- **Why the rule is shell-free.** The first cut accepted "side-effect-free" shell commands. Two
  fresh-context review passes then found 14 ways to execute or write through them:
  - command substitution;
  - `bash <script> -c`;
  - a path-qualified `cat`;
  - `PATH=` / `BASH_ENV=` assignments;
  - `rg --hostname-bin`;
  - `sed … -i`;
  - codex `apply_patch` and MCP entries;
  - agy steps with no index, a reused index or an unknown step type;
  - orphan grok updates.

  A shell denylist leaks, so the lazy pass now trusts none of it. Most of those shell bypasses also
  touch the pre-existing "is this an adapter read" classification. That is a separate, older
  residual of D10 and is out of scope here.
- A third review pass found no lazy-pass bypass that executes or writes. It raised two LOW gaps,
  and both are now closed:
  - A grok orphan update of any status, not only `completed`, is unmapped (case `grok-L3`).
  - **The `SKILL.md` read could be faked.** This one predated the change and affected the full
    PASS too: `codex-S3` was a full `PASS V-11.1`. A path now names the file only if it resolves
    to `<root>/h-mad/<file>`, and agy `view_file` counts only `FilePath` or `AbsolutePath`.

    Only a literal absolute path skips the shell-state check. A relative path, a `~` path and
    `$HMAD_SKILL_ROOT` count only in an untainted shell. Any command that is not a read or safe
    command taints what follows, including a bare assignment and `printf -v`. Each codex exec is
    fresh; agy and grok shells may persist.

    This is an allowlist because two more review passes broke the denylist versions:
    - 9 of 14 cwd decoys (`builtin cd`, `{ cd; }`, `eval cd`, `. script`, …);
    - then `HOME=`/`export HOME=`/`printf -v HOME` turning `~` into a decoy;
    - then the name spelled apart (`HMAD_SKILL''_ROOT=`, `${n}_ROOT=`);
    - then the "literal" absolute path itself: `<root>/h-mad/$X/../SKILL.md`, and a glued zsh
      modifier `SKILL.md(:s/skills/decx/)`. A shell path now counts only if it is spelled from
      `[A-Za-z0-9_./-]` (optional leading `~/`); a glued `(` splits off as a second command;
    - then output attribution, which predates this change (HEAD passes these logs too):
      `cat <file> >/dev/null; cat <decoy>`, `test … && cat <file>; echo '<heading>'`,
      `nl -s <file> <decoy>` and `head -c 0`. A shell read is now credited only as the exec's sole
      command, with one operand and no option except head/tail `-n N` and sed's print-only flags.
      (Dropping the one-operand limit on a "printed whole" argument was wrong: a fifth pass showed
      `head -n 1 <file> <decoy>`, `tail -n 1` and `sed -n '$p'` taking the heading from the
      decoy, on real zsh output.)

    - then a reader redefined in a persistent agy or grok shell (`cat() { … }`,
      `export PATH=…`), which a literal absolute path did not escape. A tainted shell now credits
      no read at all.

    All 35 decoys now fail. The legitimate spellings pass: an absolute path, the `~` installed
    link, and a fresh exec after an earlier `cd`. Cases `*-S1`–`S37` cover this (n=147). Every guard was
    mutation-killed; S27–S29 pin the taint and path-charset guards in a persistent agy shell,
    where the sole-read rule alone does not reach. Five redundant clauses survived their probes
    and were removed: a later-command assignment taint; a separate glued-`(` guard (the split
    makes the read non-sole); a no-redirect check (a sole read's stdout can only come from its
    operands); a separate option refusal (any option lands among the operands and fails the
    one-operand limit); and a codex-only lazy guard.

    **Both LOW residuals are now closed (same day).**
    - *Machine dependence.* The verdict no longer asks the scoring machine anything. Paths
      compare as normalised text against `<root>/h-mad/<file>` and the `--link` loader links,
      `~/` and `$HOME/` expand only with `--home`, and `..` is refused. The plan and design
      smoke now pass `--home "$HOME" --link "$L"`; the smoke verified `$L` with `readlink -f`
      before the run.
    - *Codex symlink across execs.* A link read, and `$HMAD_SKILL_ROOT`, also need an untouched
      filesystem. Anything earlier in the whole log that was not proven read-only (an unmapped
      tool, a non-read/safe command) forfeits them. Unlike the shell taint, this one never
      resets.

    A seventh review pass found that only link reads needed the clean filesystem. A `cp` over
    the checkout file, or `echo … > h-mad/SKILL.md` (a redirect through a safe command, which the
    tokenizer drops), was still credited. Every credited read now needs an untouched filesystem,
    and any output redirect taints it. grok's read-only `grep` tool and
    `cd`/`pushd`/`popd`/`pwd` do not taint it. Scored with all three verified loader links, the
    retained live logs give the recorded verdicts: grok PASS, codex UNVERIFIED, agy FAIL. The
    live grok run read its skill through the codex link `~/.agents/skills/h-mad`, so the smoke
    now verifies and passes all three links. An absolute read in a codex exec whose cwd is not
    the root now counts; only relative paths need the root cwd.

    An eighth pass then found hidden commands inside safe ones: ``echo `cp …` `` and zsh's
    `echo ${PATH::=…}`. A ninth pass found zsh math assigning variables, through
    `printf %d HOME=7` and `$[HOME=7]`. An exec with any active expansion (a backtick, `$(`,
    `$[`, or a braced parameter with an operator) now taints both the shell and the filesystem.
    `printf` is no longer a safe command. A tenth pass found that zsh subscript math
    (`$PWD[HOME=7]`) assigns through plain-looking syntax. The pattern list therefore became an
    allowlist: any `$` other than a plain `$NAME`/`${NAME}` with no subscript, and any backtick,
    is active.

    The character allowlist became redundant under the text comparison and was removed. Cases
    `*-G1`–`G18` cover this; they use a fake `HOME`, so the rehearsal passes unchanged under
    another `HOME` and working directory (n=166). A cache-proof mutation sweep, with each mutant
    in its own module and no bytecode, kills all 36 guards. An earlier ad-hoc sweep had reused a
    stale `.pyc` between mutants of equal size written in the same second, and reported one kill
    that was not real. The repo's own harness already guards against this
    (`h_mad_mutation_harness.py` clears `__pycache__`).

    Still not credited, conservatively: `cd <root> && cat …`, and a read with its own prefix
    assignment.

    An eleventh review pass found no new decoy. A **fresh** reviewer, with no history, then
    found four more from angles the long-running reviewer had not tried:
    - `bash /dev/stdin -c '…'` runs stdin, not the `-c` text;
    - a reused grok `toolCallId`;
    - a non-tool agy step on a tool step's index supplying its output;
    - an agy `view_file` whose `FilePath` and `AbsolutePath` name different files.

    All four are closed (cases `F1`–`F5`, n=171).

    A second fresh reviewer found two more. `rg --hostname-bin` runs a program on the full-PASS
    path; the earlier fix covered only the lazy pass, so `rg` is no longer a safe command. And
    `sed_safe` stopped checking at the first operand, while GNU sed runs a later `-e w`/`e`
    script; it now checks every argument. Cases `F6`–`F8` cover these (n=174), and a
    cache-proof sweep kills 42/42 guards. That reviewer's other finding, codex output forging
    whole `exec` blocks, is the documented design residual.

    A third fresh reviewer found three more:
    - `[ -v 'x[HMAD_SKILL_ROOT=5]' ]` assigns through subscript math (`test`/`[` are no longer
      safe);
    - `HMAD_HOST=codex HMAD_HOST=agy` counted as declared, although the last assignment wins;
    - `python3 - h_mad_x.py` counted as a script run, although it runs stdin.

    It also noted that with any `-e`, GNU sed reads `1p` as a file. Cases `F9`–`F12` cover these
    (n=178), and a cache-proof sweep kills 46/46 guards. **Residual, LOW (environment):** the log cannot
    show what the host shell sources before the first command. `zsh -lc` reads the login profile,
    which could `cd`, define functions or set `RIPGREP_CONFIG_PATH`/`GREP_OPTIONS`. The checker
    trusts the session's starting environment, which the smoke's operator controls.

- Fifteen rehearsal cases were added (`*-L*`, n=93 → 108). Each guard was mutation-probed and
  killed. A codex-only guard survived its probe because the shell rule subsumes it, so it was
  removed.
- The spec's V-11.1 clause carries the exception.
- `h-mad/SKILL.md` §"Host runtime" states the rule, and now times the agy adapter read "before
  bootstrap", as it already did for codex and grok.

**Re-scored: the agy row stays FAIL, and the reason is now settled.** The live agy log had
survived in the original session's scratchpad. It is now committed as
`rehearsal/live-agy-2026-10-01.log`, case `live-agy-2026-10-01`, so it cannot be lost again.

Under the lazy rule it scores `FAIL V-11.1 no adapter read`. That is because it was **not** a
read-only status call:

- agy ran 15 shell commands before it ever read the state file. These included `find /`,
  `zsh -i -c "type h-mad"`, `HMAD_HOST=agy h-mad status …` and a nested
  `HMAD_HOST=agy agy /h-mad status …`.
- It read `SKILL.md` at step 9. It then searched for an `h-mad` binary instead of following the
  adapter instruction.
- It reached the answer by `cat docs/.bkit-memory.json`.

The status line was still correct, and nothing was written (V-11.2 and V-11.3 PASS). The FAIL is
the one the new rule exists for: a call that runs commands without the adapter.

Two more things the re-score surfaced:

- The live log carries two `system_message` steps, a harness notice with no tool and no
  parameters. That type is now on the non-acting list (case `agy-L12-system-message`, n=110).
  Without it, every real agy log would fail closed.
- The smoke script's V-11.1 assertion in plan §"The smoke script" and the matching design block
  compared `= "PASS V-11.1"` exactly. Both now accept the lazy token too, so a lazy pass is no
  longer reported as a stop.

## Addendum 2026-10-01 (later): only a file-read tool proves a read

**Operator decision.** Shell reads no longer earn V-11.1 credit. The rule history above, from
the lazy-pass shell rules to the plain-parameter allowlist, is superseded where it concerns
crediting a shell read. Fourteen review rounds, three of them from fresh-context reviewers, each
found three or four new ways for a command rated read-only to run code or assign through zsh.
An allowlist over shell text could not be shown complete; removing shell credit removes the
problem at its source.

- **Codex** has no file-read tool, so its verdict is always
  `UNVERIFIED V-11.1 codex has no file-read tool` (or a shape error). Its live run was already
  `UNVERIFIED`.
- **agy `view_file` and grok `read_file`** are the only credited reads. They still require the
  lexical path match against `<root>/h-mad/<file>` or a verified `--link`, an untouched
  filesystem, and the event-shape checks. Shell commands still feed the filesystem taint, the
  script-before-adapter ordering and the `HMAD_HOST` declaration.
- **Removed as dead code:** the shell-read credit path, the sole-read and one-operand rules, the
  shell-state taint, the cwd plumbing, and `lexical()`'s `~`/`$HOME` expansion. The 41 codex
  shell-decoy cases went with them.
- **New pins:** thirteen agy cases (`P1`–`P13`) re-pin the filesystem taint, `dotdot` and the
  script-detection guards, which the codex cases used to pin. Rehearsal n=150, and the
  cache-proof mutation sweep kills 36/36 guards.
- **Live verdicts are unchanged:** grok PASS, codex UNVERIFIED, agy FAIL.

A fresh review of the file-tool-only rule found writes and shapes the taint still missed. A read
is now ordered by *completion* (a write issued while it was outstanding voids it). Prefix
assignments other than `HMAD_HOST` and path-qualified commands taint. Unknown grok rows and agy
events, a grok update carrying `rawInput`, and a second terminal update are all refused. A script
run declaring another `HMAD_HOST` FAILs. A partial read still counts, as the original documented
residual. Cases `V1`–`V10` cover these (n=164), the cache-proof sweep kills 42/42 guards, and the
live verdicts are unchanged.

A further fresh review found that `taints()` was still trying to tell which shell commands write.
`cat < <(cp …)` and `cd /tmp;<(cp …)` slipped through. Every shell command now counts as a
possible write: a file-tool read counts only if it completes before the host's first shell
command. The live grok run did exactly that, and it still passes. The write classifier (the
expansion allowlist, the `cd` exemption, prefix and path checks) is deleted. Any `HMAD_HOST=`
naming another host, in any spelling, FAILs. The design cases `R7-sed`/`R7-grep` (a shell
`sed`/`grep` before the reads) now FAIL, which is the accepted cost. n=170, and the cache-proof
sweep kills 32/32.

The next fresh review found that the `HMAD_HOST` declaration was still read with a regex over
shell text: `HMAD_HOST=grok"agy"`, `HMAD_HOST+=agy` and `read`/`export` fooled it. Now only a
script's exact prefix token counts; any other value of that token FAILs, and any other occurrence
of `HMAD_HOST` makes the declaration `UNVERIFIED`. An agy step with no `ACTIVE` row now counts as
issued at the start of the log. 38 agy fixtures were normalised to real `ACTIVE`+`DONE` pairs. A
non-string row type no longer crashes the checker. n=176, the cache-proof sweep kills 35/35 (the
harness now counts a crashing mutant as killed), and the live verdicts are unchanged.

Review round 18 (a fresh-context reviewer, 2026-10-01) found six fail-opens, two crashes and four
smaller defects, each with an executed fixture and a control. The report and its generators are
in `docs/03-analysis/probes/multi-host-runtime/review-r18/`.
- **The declaration (H1, H2, and a spec gap).** Text that never runs still counted as a run: a
  comment, a heredoc body, `false && …`, `python3 -X`, `bash -o -c`. Environment changes that do
  not spell `HMAD_HOST` slipped past the mention count: `HMA""D_HOST`, a function wrapping
  `python3`, `${n}_HOST`. By operator decision, the declaration is now judged only when every
  shell event is a plain command list, defined by a positive grammar (see the spec). Otherwise it
  is `UNVERIFIED … declaration not in a plain command list`.
- **Ordering (H3).** A grok update before its `tool_call`, and an agy `DONE` before its `ACTIVE`,
  are now shape errors instead of an early completion.
- **Shapes (H4, H5, M1, L3).** These are now `UNVERIFIED`: a non-object agy `step_update`, a
  non-string `FilePath`/`AbsolutePath`, a non-string `toolCallId`, a non-integer `step_index`,
  and a non-tool step that names a tool. The first two passed before, and the last two crashed
  the checker.
- **Parsing (H6, M2, L1).** A duplicate JSON key, a row that is not UTF-8, and an oversized
  integer are now `unparseable line N`. Rows are split on `\n` only, so a raw U+2028 or U+0085
  no longer breaks a row.
- **Links (L2).** A relative `--link` is ignored, since it resolved against the scorer's cwd.

A self-review of the fix found one more fail-open, this time inside the plain grammar.
`HMAD_HOST=agy python3 -X h-mad/scripts/…` and `HMAD_HOST=agy bash -o -c h-mad/scripts/…` use
only plain characters, yet `classify` read each as a script run. Live, neither runs the script.
`classify` now handles the options as the interpreters do:
- python `-W`/`-X` take the next word;
- a short cluster holding `c` or `m` ends operand search;
- a long option is not followed;
- for bash and zsh, an option cluster with `o`/`O`, a `+` option or a long option before `-c`
  is not followed.

Cases `R18-*` (43) bring n=219. Every one of the 176 existing expectations still holds. Two
existing verdicts changed on the reviewer's clean probes, both deliberately:
`HMAD_HOST=ag"y"` and `"HMAD_HOST=agy" S` are now `UNVERIFIED`. The cache-proof mutation sweep
over the 23 new guards caught every mutant:
- 21 were killed by a wrong verdict.
- 2 (the `toolCallId` and `step_index` type checks) were killed only by a crash. Removing either
  check reopens the `TypeError` that M1 reported, so these kills are visible but are not verdict
  kills.

The sweep's first harness crashed on load and showed every mutant as killed. A control mutant
(the unmodified source) now runs first and must pass. The live verdicts are unchanged: grok PASS,
codex UNVERIFIED, agy FAIL.
