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
    whole `exec` blocks, is the documented design residual. **Residual, LOW (environment):** the log cannot
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
