# Spec: tdd-gate-fail-opens

## Executive Summary

Both H-MAD Phase-5 TDD gates, `h-mad/hooks/h-mad-tdd-gate.sh` (Claude Code) and
`h-mad/hooks/h-mad-codex-tdd-gate.py` (Codex), must decide a write by the **identity** of the file it
lands in, never by how the target is spelled. Today five reproduced defects (D1–D5, gap report
`docs/archive/2026-09/codex-tdd-gate-defects/codex-tdd-gate-defects.gap.v1.md` §"Defects
(reproduced)") let a governed production write through during `step5` with no measured failing
test, or let the judge overrun its budget. This spec closes them with one target-normalisation rule
shared by both gates (D1, D3, D4), a Codex patch-header grammar that matches Codex's own parser
(D2), and a bounded post-kill reap in the shared judge that reports a distinct `judge-timeout`
kind (D5). A cross-gate differential pins that both gates return the same decision for the same
spelling, so the D4 class cannot return.

It also closes one carried defect that the operator folded in (OD-6, FR-8). The Codex gate's shell
policy refuses the documented resume oracle, `h_mad_resume_decision.py`, while any feature on the
state chain is in `step5`. As a result a Codex-hosted `/h-mad` cannot run it there.

## Goal

While a feature is in `step5`, every spelling of a governed production Python file — case variant,
symlinked directory, symlinked root, `..` after a symlink, padded patch header — is refused by both
gates exactly as its canonical spelling is. A spelling that cannot be resolved is refused
`judge-error`. The judge never waits past its budget plus one bounded reap grace. A Codex-hosted
`/h-mad` can run the resume oracle in its documented form while the gate is armed.

## Binding decisions and where this spec goes beyond them

The brainstorm (`docs/01-plan/features/tdd-gate-fail-opens-brainstorm.md` v1.1, commit `c83c62fe`)
is operator-approved. The orchestrator relayed seven binding decisions (operator, 2026-09-29):

| # | Binding decision | Where this spec states it |
|---|---|---|
| B1 | Scope is D1–D5, all five. | FR-1…FR-5 |
| B2 | D4: resolve first in **both** gates, by one target-normalisation rule (realpath the target including the deepest existing ancestor plus the remainder for a new file; physical root; inside-root on the resolved pair; directory and basename exemptions on the resolved target). | FR-1 |
| B3 | D1: case-fold the `.py` suffix; any case is production; fail-closed. Residual: a legitimate `*.PY` data file is refused. | FR-2 |
| B4 | OQ1: an unresolvable symlink target (dangling or loop) is refused `judge-error`, never treated as not-a-file. | FR-3 |
| B5 | OQ2: a D5 reap failure is a distinct DENY kind `judge-timeout`, separate from `timeout`. | FR-5 |
| B6 | D2: the Codex gate strips trailing whitespace and `\r` from `*** Add/Update/Delete File:` and `*** Move to:` header paths per Codex's `apply_patch` grammar, and refuses (`judge-error`) a header path that still carries a control byte. | FR-4 |
| B7 | Every gap-report repro becomes a pinned test on the relevant gate(s), plus a shared cross-gate differential (same spellings, same decision). | FR-6 |

Measuring the tree for this spec found members of the same classes that B2 and B6, **read
literally**, do not close. Each is written below as an operator decision (OD) with the resolution this
spec uses so its ACs are testable. None weakens B1–B7; each one refuses more or decides by identity
where the binding text decides by spelling. The operator approved OD-1…OD-5, each with the
resolution below, on 2026-09-29 (commit `662b1ce1`). OD-6 is different. It is not a gap in B1–B7.
It is a carried defect outside B1's D1–D5 scope, which the operator decided on 2026-09-29 to fold
into this feature. It is also the one OD that moves a verdict toward ALLOW for a shell command, and
only for one read-only script.

| OD | Gap in the literal decision (measured, §"Measured premises") | Resolution this spec uses |
|---|---|---|
| OD-1 | B2 says "realpath the target" and "physical root". `os.path.realpath`, `pathlib.Path.resolve` and bash's builtin `pwd -P` all **keep the spelled case** of an existing component; `getcwd()` (and `/bin/pwd -P`) and macOS `fcntl(F_GETPATH)` return the **on-disk** spelling. Two fail-opens survive a realpath-only rule: M-8 (root and target spelled in different case: Claude gate ALLOW, Codex gate DENY) and M-9 (on-disk directory `Tests/` spelled `tests/`: **both** gates ALLOW). | The canonical form of every **existing** component, in the root and in the target, is its on-disk directory-entry spelling, produced by one primitive shared by the root and the target (FR-1). This is a verdict change toward ALLOW in one case (M-10), stated in FR-1. |
| OD-2 | B6 names **trailing** whitespace. Codex 0.158.0 trims **both** ends of a header line, with the Unicode `White_Space` set, before matching the marker. An indented header after a normal one is accepted by Codex and missed by the gate's `^\*\*\* ` anchor, so the patch is allowed (M-17). Trailing U+00A0, U+3000, U+2028, VT and FF are trimmed by Codex and not by the gate (M-15). | The gate recognises a header on a line trimmed at **both** ends with exactly Codex's whitespace set, then refuses a remaining control byte (FR-4). |
| OD-3 | B3 says any-case `.py` is production. It does not say whether the basename exemptions (`test_*.py`, `*_test.py`, `conftest*.py`) see the folded suffix. The two gates spell the exemption differently (`test_*.py` glob vs `name.startswith("test_")`), so leaving it open lets them disagree on `test_x.PY`. | The `.py` fold happens **before** every name test: production classification and all three basename exemptions run on the name with its suffix folded to `.py`; the stem stays case-sensitive (FR-2). |
| OD-4 | B4 does not say when an unresolvable target is refused. Refusing it in a repository with no `step5` state would change every non-H-MAD repository. | The refusal applies only when H-MAD state governs the target (`active` or `unreadable`); with no governing state the gate allows, exactly as today (FR-3). It applies to **any** suffix, because an unresolvable link's own name says nothing about its referent. |
| OD-5 | B7's differential ("same spellings, same decision") would fail on divergences that the predecessor feature specified on purpose: an exempt write on an unreadable chain (Claude allows, Codex refuses — predecessor OD-A), an outside-root target (Codex refuses every file type; Claude governs only `.py`), and relative targets (Claude joins the root, Codex joins the payload `cwd`). | The differential's domain is absolute in-root spellings over a readable chain (FR-6). "In-root" is decided in one of two ways. For a resolvable spelling, the canonical target must be inside the canonical root. For an unresolvable spelling (FR-3), which has no canonical target, its **resolved prefix** must be inside the canonical root. The resolved prefix is the longest spelled prefix that FR-1 step 2 walks before FR-3's predicate holds. Both gates must then agree on decision and kind. Every required cell, M-12–M-14 and M-18 included, is in the domain. The three excluded divergences, and the unresolvable spellings that fall outside the domain, are listed under "Residuals", each with the reason it is out of domain. |
| OD-6 | Not a gap in B1–B7: this is a carried defect folded into this feature. The Codex gate's `SAFE_HMAD_SCRIPT_OPTIONS` has no entry for `h_mad_resume_decision.py`. The three host adapters document `--session-id "$(cat …)"`, and `$(` fails `SIMPLE_SHELL_COMMAND`. So while any feature on the chain is in `step5`, a Codex-hosted `/h-mad` cannot run the documented resume oracle. This is live wherever the gate is armed, HemaSuite included (`h-mad/references/grok-runtime.md` §"The TDD gate" names HemaSuite's tracked `.codex/hooks.json`). | Operator decision 2026-09-29: fold it in (FR-8). The safe list admits the script with exactly its parser's long options. The script gains `--session-id-from-git-dir`, which reads the minted id file itself, so the documented command has no command substitution. The three adapters' oracle line moves to that form. |

## Measured premises

Reading taken 2026-09-29 at skills `1a77e1c4` (the three code files are byte-identical to
`c83c62fe`: `git diff --stat c83c62fe HEAD -- h-mad/hooks h-mad/scripts/h_mad_tdd_judge.py` is
empty), macOS 27.0, APFS (case-insensitive, the default), Python 3.14.7, codex-cli 0.158.0. The gap
report measured codex 0.157.1; every D2 cell it reported reproduced unchanged on 0.158.0. The
scratch probes were deleted after running; the committed re-run is **owed** at
`docs/03-analysis/probes/tdd-gate-fail-opens/reproduce.py` (orchestrator). That probe drives only
the two gates and the judge and never invokes `codex` (plan PD-4; `h-mad/invariants.base.md`
§"Dispatched agent CLIs are not script dependencies"), so it re-derives the **gate** columns only.
The "Codex writes" column of M-15…M-23, Codex's trim set and Codex `apply_patch` following a leaf
symlink come from the plan's **manual** R-4 reading, and the Claude Code leaf-symlink rows from its
manual R-5 reading; T0 enters each as a manual row carrying its exact command, tool version and
date. Neither reading exists in committed form yet (plan PD-4, task T0), so these tables stay until
T0 commits its unfixed reading, and are then replaced by a pointer to that one reading **together
with its manual R-4 and R-5 rows**.

Fixture for M-1…M-14 and M-18: a git root with `src/prod.py`, and `docs/.bkit-memory.json` =
`{"orchestrator_state":{"feat":{"phase":"step5","codex_status":"exhausted"}}}` (so the Claude
gate's Codex-authorship check steps aside and the judge decides). Claude-gate payload
`{"tool_name":"Write","tool_input":{"file_path":<abs>}}` with `CLAUDE_PROJECT_DIR=<root>`;
Codex-gate payload `{"tool_name":"Write","cwd":<root>,"tool_input":{"file_path":<abs>}}` with
`CODEX_PROJECT_DIR=<root>`. "deny K" means a deny JSON whose reason carries `kind=K`; "deny
outside" is the Codex gate's kind-less "write target is outside or unreadable" denial.

| Id | Spelling (absolute unless stated) | Claude gate today | Codex gate today | Class |
|---|---|---|---|---|
| M-1 | `src/prod.py` (control) | deny no-test-resolved | deny no-test-resolved | — |
| M-2 | `src/prod.PY`, `prod.py` exists | ALLOW | ALLOW | D1 |
| M-3 | `src/new.PY`, absent | ALLOW | ALLOW | D1 |
| M-4 | `tests/prod.py`, `tests -> src` | ALLOW | deny no-test-resolved | D4 |
| M-5 | `tests/newmod.py`, `tests -> src`, absent | ALLOW | deny no-test-resolved | D4 |
| M-6 | `tests/l/../prod.py`, `tests/l -> ../src/sub` | ALLOW | deny no-test-resolved | D4 (`..` after a symlink) |
| M-7 | root spelled `R/tests/link` (`-> R/real`), target `R/tests/link/x.py` | ALLOW | deny no-test-resolved | D3 |
| M-8 | root `…/Case/tests/proj`, target `…/case/tests/proj/src/prod.py` (and the reverse) | ALLOW | deny outside | OD-1 |
| M-9 | on-disk `Tests/prod.py`, spelled `tests/prod.py` | ALLOW | ALLOW | OD-1 |
| M-10 | on-disk `fixtures/helper.py`, spelled `FIXTURES/helper.py` | deny no-test-resolved | deny no-test-resolved | OD-1 (fail-closed today) |
| M-11 | `src/tl/helper.py`, `src/tl -> ../tests` | deny no-test-resolved | ALLOW | D4 (reverse direction) |
| M-12 | `docs/d.md -> ../src/newprod.py` (dangling) | ALLOW | deny no-test-resolved | B4 |
| M-13 | `src/dang.py -> nowhere/x.py` (dangling); `lnk/x.py`, `lnk -> nowhere` | deny no-test-resolved (both) | deny no-test-resolved (both) | B4 |
| M-14 | `src/loopa.py -> loopb.py -> loopa.py` (loop) | deny no-test-resolved | deny no-test-resolved | B4 |
| M-18 | M-13 and M-14 under a state file holding only a `step3` record | ALLOW | ALLOW on M-13; deny judge-error on M-14 (fixed: allow, the approved change in FR-1 "Verdict changes toward ALLOW") | OD-4 control |

Codex patch headers (Codex gate, `apply_patch` payload `{"tool_name":"apply_patch","cwd":<root>,
"tool_input":{"command":P}}`; "Codex writes" = codex-cli 0.158.0's own `apply_patch` invoked as
`argv[0]=apply_patch` in a scratch copy of the fixture, a manual reading (plan R-4) that no
committed probe or test re-derives):

| Id | Header in P | Codex gate today | Codex writes |
|---|---|---|---|
| M-15 | `*** Update File: src/prod.py` + one of: `\r` (CRLF patch), space, tab, U+00A0, U+3000, U+2028, U+0085, U+2003, VT, FF | ALLOW for CRLF, space, U+00A0 (each run); tab/VT/FF/U+3000/U+2028/U+0085/U+2003 not run through the gate — each leaves a non-`.py` suffix by the same mechanism | `src/prod.py` modified, every variant |
| M-16 | leading space or tab before `*** Update File: src/prod.py`, alone in the patch | deny "could not identify this write target" | `src/prod.py` modified |
| M-17 | `*** Add File: docs/x.md` then an indented `  *** Update File: src/prod.py` | **ALLOW** | both files written; `src/prod.py` modified |
| M-19 | `*** Update File: docs/a.md` + `*** Move to: src/prod2.py ` (trailing space) | ALLOW | `src/prod2.py` created |
| M-20 | `*** Add File: src/n.py` + U+001F | ALLOW | `src/n.py\x1f` created (U+001F is **not** trimmed) |
| M-21 | trailing or leading U+001C, U+001E, U+200B, U+FEFF | — | not trimmed: update fails, no write |
| M-22 | `*** update file:`, `***  Update File:`, `*** Update File:src/…`, `**** Update File:`, `*** Update File:\tsrc/…` | — | rejected as an invalid hunk: the marker is matched **exactly** |
| M-23 | leading space before `*** Move to: src/new.py` | — | not taken as a move; update fails |

Codex's trim set, measured: it trims U+0009, U+000B, U+000C, U+000D, U+0020, U+0085, U+00A0, U+2003, U+2028, U+3000
and does not trim U+001C, U+001E, U+001F, U+200B, U+FEFF. That is the Unicode `White_Space`
property (Rust `char::is_whitespace`), which equals Python `str.isspace()` **minus U+001C–U+001F**.
The code points not run are inferred from the property, not measured. The trim set is a manual
reading (plan R-4), not an output of T0's committed probe.

Canonicalisation primitives (a directory `Case/` spelled `case/`; a directory stored NFD, spelled
NFC): `os.path.realpath`, `Path.resolve` and bash builtin `pwd -P` return the spelled form;
`os.getcwd()` after `chdir`, `/bin/pwd -P` and `fcntl(fd, F_GETPATH)` return the on-disk form (case
and NFD). `os.path.realpath` (non-strict) on a symlink loop **returns the lexical path without
error**; `os.path.realpath(p, strict=os.path.ALLOW_MISSING)` raises `OSError` errno 62 (ELOOP) on the
loop and follows a dangling link to its (absent) referent.

An existing directory the primitive cannot open (OQ-P1; measured 2026-09-29 at skills `f5e44a50`,
Python 3.14.7, in a `TemporaryDirectory`, scratch probe deleted after running): on-disk `Tests/` at
mode 0311, spelled `tests/`. `os.path.exists` and `os.path.lexists` are both true; `os.open(…,
O_RDONLY)` on the directory and `os.listdir` both fail with errno 13 (EACCES); creating
`tests/new.py` in it **succeeds**; an existing `tests/prod.py` inside it still opens, and `F_GETPATH`
on that file returns the on-disk `…/Tests/prod.py`. So the writer can create in a directory whose
on-disk spelling the primitive cannot read from the directory itself, and a spelling fallback there
would exempt it (M-9's class). T0's probe owes this cell.

Writers and a leaf symlink `src/link.py -> ../tests/t.py`: Codex `apply_patch` "Update File:
src/link.py" **follows** the link (the link survives, `tests/t.py` is modified). The Claude Code
Write tool of the build that authored this spec refused the write ("it is a symbolic link. Write
to the link's target path instead"). **Edit** (PD-5, measured live by the orchestrator on Claude Code
2.1.284, 2026-09-29) is refused by the tool itself ("Refusing to write …: it is a symbolic link.
Write to the link's target path instead: …"); the link and `tests/t.py` are unchanged. MultiEdit and
NotebookEdit are not in that build's tool set, so they are **unmeasurable** there, not measured. No
tool observed replaces the link, so FR-1's leaf rule stands unamended. These rows are harness-tool
actions: T0's `reproduce.py` cannot re-derive them, and they enter T0's reading only as manual rows
carrying the build and date above.

D5: `h_mad_tdd_judge._run_bounded([python, "-c", "Popen(['sleep','12'], start_new_session=True);
sleep(30)"], ., now+2.0)` → `elapsed=12.0 timed_out=True rc=-9` (the gap report's reading,
reproduced).

Codex resume oracle (OD-6, FR-8). This reading was taken 2026-09-29 at skills `78e35abf` with
Python 3.14.7. It is a scratch probe that imported the gate from its path and called
`_safe_shell_command(command, root, cwd)`. The probe was deleted after running, and T0's probe owes
the committed cells.
- `SAFE_HMAD_SCRIPT_OPTIONS` has 10 keys, and `h_mad_resume_decision.py` is not one of them.
- `h_mad_resume_decision.py`'s `main()` declares five long options besides `--help`: `--state`,
  `--feature`, `--host`, `--session-id` and `--now`.
- The oracle line under §"Context budget and claims" in `h-mad/references/codex-runtime.md`,
  `grok-runtime.md` and `agy-runtime.md` passes `--session-id "$(cat "$(git rev-parse
  --absolute-git-dir)/h-mad-session-id.<feature>")"`.

The gate results on the unfixed tree:
- the documented line: `SIMPLE_SHELL_COMMAND.fullmatch` is `None` and the result is `False`;
- the same line with a literal uuid as `--session-id`: `False`, because there is no map entry;
- `git rev-parse --absolute-git-dir`: `False` (`git` is not in `READ_ONLY_COMMANDS`).

With an in-memory entry of FR-8's six options:
- the literal-uuid form and the `--session-id-from-git-dir` form: `True`;
- the documented `$(` form: still `False`;
- `-h`, `--bogus x`, and a `~/…` script path: each `False`.

## Terms

- **Spelling**: the target string the gate receives (Write/Edit `file_path`, or a patch header
  path), and the root string (`CLAUDE_PROJECT_DIR`, `CODEX_PROJECT_DIR`, or the Codex fallbacks).
- **Canonical form**: FR-1's output. For an existing component, its on-disk directory-entry name
  after every symlink is followed; for the non-existing remainder, the spelling.
- **Governed**: on the Claude side, the judge's `state` verb (chain reader
  `h_mad_tdd_judge.read_chain`) reports `active` or `unreadable` for the target; on the Codex side,
  `_any_phase5_status` reports `active` or `unknown` (the rule the Codex gate already applies to an
  outside-root target and to an unidentified target).
- **Unresolvable**: FR-3's predicate.

## Functional Requirements

### FR-1: One target-normalisation rule in both gates (D3, D4; B2, OD-1)

- **Description**: Before any exemption, suffix test or inside-root test, each gate computes the
  canonical form of the root and of the target, and decides only on those. The rule is identical in
  both gates:
  1. **Absolute join.** A relative target is joined to its base exactly as today (Claude: the root;
     Codex: `_payload_cwd_base`). No lexical `..` collapse happens before step 2.
  2. **Deepest existing ancestor.** Walk the target's components from the left, asking the kernel
     at each prefix (so `..` is taken after the preceding symlink, as the kernel takes it; out of
     an existing non-symlink directory `..` is its lexical parent, which is not opened; `.` components
     are dropped from the walk first, so a `.` never absorbs the next `..` — v1.6, N-1). The
     prefix where the next component does not exist splits the target into an existing part and a
     remainder. If FR-3's predicate holds at any prefix, stop: the target is unresolvable.
  3. **Canonicalise the existing part** with every symlink followed and every component rendered in
     its **on-disk spelling** (case and Unicode normalisation as stored). The root is canonicalised
     by the **same primitive**, and so is the Codex payload `cwd` before `_payload_cwd_base` tests
     containment. A spelling-preserving primitive (`os.path.realpath`, `Path.resolve`, bash builtin
     `pwd -P`) does **not** satisfy this step: M-8 and M-9 fail with it. If the primitive cannot
     open or list an existing component this step or step 4 needs, FR-3's second arm applies; the
     gate never falls back to the spelling for that component.
  4. **Existing leaf.** If the leaf exists, its on-disk name is the entry of its canonical parent
     directory that has the leaf's `(st_dev, st_ino)`. If several entries in that directory share
     it (hard links in one directory), an exemption holds only if it holds for **every** such
     entry.
  5. **Remainder.** Append the remainder in its spelling, then collapse `.` and `..` lexically. A
     `..` inside the remainder follows a component that does not exist, so the kernel would fail the
     write with ENOENT; the verdict for such a target is inert.
  6. **Inside-root** is decided on the canonical pair only. Directory exemptions (`tests`,
     `fixtures` components) run on the canonical path **relative to the canonical root**; basename
     exemptions and the `.py` test (FR-2) run on the canonical leaf.
  7. An outside-root target keeps each gate's current outside-root rule, with the canonical target
     in place of the target that rule reads today (Claude: the `normpath`'d `TARGET_PATH`, the line
     tagged `# M:H20`, which also requires the raw spelling to match; Codex: `_relative_target`
     returns `None` and the write is refused when governed).
  8. The judge receives the canonical root and target (`--root`, `--target`); its own
     `os.path.realpath` calls are then identities.
- **Verdict changes toward ALLOW** (identity, not weakening; each lands the write in an exempt
  location): M-10 (both gates), M-11 (Claude gate; the Codex gate already allows), and a leaf
  symlink into `tests/` (Claude gate; Codex already follows it). One further change is not an
  exempt-location identity and is approved separately (operator, 2026-09-30): the Codex gate on
  M-18's M-14 case (the loop under the `step3`-only state; probe key `cell=M-18 M-14 gate=codex
  state=step3`) moves deny `judge-error` → allow. The unfixed reading
  (`docs/03-analysis/probes/tdd-gate-fail-opens/reading-unfixed.txt`, committed at `a737962a`)
  has the Codex gate deny it and the Claude gate allow it; `step3` is ungoverned, so the unfixed
  Codex gate was refusing a symlink loop outside Phase 5 (also observed in
  `docs/03-analysis/probes/tdd-gate-fail-opens/t6-unfixed-differential.txt`).
- **Acceptance Criteria** (fixture as in §"Measured premises"; "fixed"/"unfixed" name the observable
  that differs):
  - AC-1.1 (D4): M-4 and M-5 — fixed: the Claude gate denies with the same kind as M-1
    (`no-test-resolved`); unfixed: rc 0, no stdout.
  - AC-1.2 (D4, `..`): M-6 — fixed: Claude gate deny `no-test-resolved`; unfixed: allow.
  - AC-1.3 (D3): M-7 — fixed: Claude gate deny `no-test-resolved`, and the control (root and target
    spelled `R/real`) denies with the same kind; unfixed: allow. The fixture's symlinked root
    contains a `tests` component, and the test asserts that precondition.
  - AC-1.4 (OD-1, case root): M-8 in both directions — fixed: both gates deny with the judge's kind
    for the canonical spelling (`no-test-resolved`); unfixed: Claude allow, Codex "outside".
  - AC-1.5 (OD-1, case directory): M-9 — fixed: both gates deny `no-test-resolved`; unfixed: both
    allow.
  - AC-1.6 (OD-1, toward ALLOW): M-10 — fixed: both allow; unfixed: both deny. M-11 — fixed: both
    allow; unfixed: Claude deny.
  - AC-1.7 (primitive): a unit test drives each gate's canonicaliser on M-8's and M-9's directories
    and asserts the on-disk spelling; with `os.path.realpath` substituted for the canonicaliser the
    same test fails (the negative control is run, not asserted).
  - AC-1.8 (new file): `src/brandnew.py` (absent, parent exists) and `src/newpkg/mod.py` (parent
    absent) — both gates deny, with no exception and no `judge-error`; the canonical form equals the
    spelled absolute path.
  - AC-1.9 (hard links in one directory): `src/prod.py` and `src/test_prod.py` are two names of one
    inode; spelled `src/test_prod.py` — fixed: both gates deny (step 4); unfixed: both allow. The
    test asserts the precondition `os.stat(a).st_ino == os.stat(b).st_ino`.
  - AC-1.10: each case-dependent AC asserts its precondition — the fixture volume is
    case-insensitive (create `a`, then `os.path.exists("A")`) — and **fails**, never skips, when it
    does not hold.
  - AC-1.11 (outside-root symlink control, step 7, the `# M:H20` raw-spelling conjunct; plan R-3):
    Claude gate, root `R`, outside-root directory `out/` with `out/lnk -> tests`; target
    `out/lnk/x.py`, whose canonical path enters `tests/` and whose raw spelling does not. Fixed:
    deny `no-test-resolved` (not exempted: the raw conjunct does not hold); unfixed: deny
    `no-test-resolved` (plan R-3's reading at `983c2f85`). The two are equal by design: this AC is
    a regression pin, and its discriminating observable is the mutant, not the unfixed tree — with
    the raw conjunct dropped (the existing `H20B` mutation in
    `h-mad/tests/mutation-specs/claude_gate_judge_wiring.json`, which keeps only the
    `$TARGET_PATH` test) the fixed gate must return rc 0 with no stdout (allow). On the unfixed
    tree `H20B` does **not** move this cell, because `TARGET_PATH` is only `normpath`'d there
    (measured 2026-09-29 at `4192ad8c`: R-3 run against a temporary copy of `h-mad/` carrying
    `H20B` printed the same three lines as the unmutated gate; copy and script deleted after
    running). So `H20B` is a valid kill only against the fixed tree. The same fixture's two
    other R-3 cells are asserted beside it: `out/tests/x.py` (raw and canonical both match) allow;
    `out/src/x.py` (neither) deny `no-test-resolved`.

### FR-2: The `.py` suffix is case-folded before every name test (D1; B3, OD-3)

- **Description**: A name is folded by replacing a final suffix that equals `.py` under ASCII case
  folding (`.py`, `.pY`, `.Py`, `.PY`) with `.py`. No other code point case-folds to `p`, `y` or
  `.` (measured over every Unicode code point with `str.casefold` and `str.lower`), so ASCII folding
  is complete for this suffix. Production classification and the three basename exemptions
  (`test_*.py`, `*_test.py`, `conftest*.py`) run on the folded name; the stem is compared
  case-sensitively, as pytest's default `python_files` does. A suffix with any other trailing byte
  (`.py `, `.py\r`) is not folded: on APFS `prod.py ` is a different file from `prod.py`
  (measured), so such a Write names a new non-Python file.
- **Acceptance Criteria**:
  - AC-2.1 (D1, existing leaf): M-2 — fixed: both gates deny with M-1's kind; unfixed: both allow.
    (FR-1 step 4 already canonicalises the existing leaf to `prod.py`; AC-2.2 is the fold's own
    pin.)
  - AC-2.2 (D1, new leaf): M-3 and `src/new.pY`, `src/new.Py` — fixed: both gates deny; unfixed: both
    allow. Each spelling is its own parametrised case.
  - AC-2.3 (OD-3): `sub/test_x.PY`, `sub/x_test.PY`, `sub/conftest.PY` (absent) — both gates allow,
    fixed and unfixed (today both allow because the name is not `.py`; the AC pins that the fold
    does not turn a test-shaped name into production). `sub/TEST_x.py` — both deny (stem is
    case-sensitive).
  - AC-2.4: `src/prod.py ` (trailing space, Write payload) — both gates allow, fixed and unfixed;
    pins that the fold is not a trim.
  - AC-2.5 (end to end, Codex): the D1 repro patch `*** Update File: src/prod.PY` — fixed: deny;
    unfixed: allow.

### FR-3: An unresolvable target is refused `judge-error` when governed (B4, OD-4)

- **Description**: A target is **unresolvable** when either arm holds:
  1. **Does not resolve.** At some prefix during FR-1 step 2, the prefix exists as a directory entry
     (`os.path.lexists`) but does not resolve (`os.path.exists` is false): a dangling symlink, a
     symlink loop (ELOOP), or a symlink whose resolution fails for another reason. It applies to a
     leaf and to an intermediate component alike.
  2. **Cannot be read in its on-disk spelling** (OQ-P1, operator decision 2026-09-29: refuse). An
     existing component of the root or of the target on which the on-disk-spelling primitive's
     operation raises `OSError` — opening it to read its on-disk path (FR-1 step 3), or listing the
     leaf's canonical parent (FR-1 step 4). Examples: a directory at mode 0311 (writable and
     traversable, not readable; measured in §"Measured premises"), and the parent of an existing
     leaf without `r`. The gate never falls back to the spelled case for such a component: that
     fallback would exempt on-disk `Tests/` spelled `tests/` (M-9's class).
  When the target is unresolvable:
  - with **governing** state (Claude: the judge's `state` verb over the target's chain reports
    `active` or `unreadable`; Codex: `_any_phase5_status` is `active` or `unknown`), the gate
    refuses with kind `judge-error` and a reason naming the unresolvable prefix;
  - with no governing state, the gate allows, as today (the Claude fast path
    `_chain_may_hold_state` and the `TDD-STATE: none` rule are unchanged).
  The suffix is not consulted: a dangling `docs/d.md` whose referent is `src/newprod.py` is refused.
  **Project root that cannot be entered** (design v1.4; operator decisions 2026-09-30, D-1/D-2/D-3):
  when the root is absent, not a directory, or not traversable (no `x`, e.g. mode 000), the state
  under it cannot be read, so whether the write is governed is unknowable. Both gates then refuse
  `judge-error` ("project root … cannot be entered") whatever the phase, before any state lookup.
  The test is on the root itself, not on the arm-2 component's spelling, so a root spelled in a
  different case from its on-disk name is refused the same way. The governed-only rule above
  applies to a root that can be entered but not listed (mode 0311). (On the Codex gate an absent
  `CODEX_PROJECT_DIR` is not a root case: the gate falls through to its next root candidate.)
  **`..` is not an arm-2 site for a plain directory** (operator decision 2026-09-30, N-1): `..`
  out of an existing non-symlink directory takes its lexical parent, which is the kernel's once `.`
  components are dropped from the walk (a kept `.` made `tests/./../src/prod.py` resolve under
  `tests/`: a fail-open present before v1.6 and fixed with it), and does not open it, so an `x`-only directory on the way does not make the target unresolvable.
  `..` out of a symlink still opens the link's referent.
  A non-strict `os.path.realpath` or `Path.resolve` alone cannot implement this predicate: on a loop
  it returns the lexical path without error (measured).
- **Acceptance Criteria**:
  - AC-3.1: M-12 — fixed: both gates deny `judge-error`; unfixed: Claude allow, Codex
    `no-test-resolved`.
  - AC-3.2: M-13 (leaf and intermediate component, each its own case) and M-14 — fixed: both gates
    deny `judge-error`; unfixed: both deny `no-test-resolved`. The kind is the discriminating
    observable.
  - AC-3.3 (OD-4 control): M-18 — fixed: both gates allow. Unfixed: both allow, except the Codex
    gate on M-14, which denies `judge-error` (the approved change in FR-1 "Verdict changes toward
    ALLOW").
  - AC-3.4: a loop fixture drives each gate's resolver directly and asserts it reports unresolvable,
    with a negative control that `os.path.realpath` of the same path returns without error.
  - AC-3.5: the Codex deny reason carries the token `kind=judge-error`; the Claude deny carries
    `BLOCK kind=judge-error`.
  - AC-3.6 (second arm, OQ-P1), under the governing `step5` state, each its own case, the fixture
    restoring the mode in teardown:
    (a) on-disk `Tests/` at mode 0311, spelled `tests/newmod.py` (absent) — fixed: both gates deny
    `judge-error`, the reason naming the component; unfixed: both allow (expected by M-9's
    mechanism, the spelled `tests` component being exempt; not yet measured, T0 measures this
    cell).
    (b) `src/` at mode 0311 holding an existing `src/prod.py`, spelled `src/prod.py` — fixed: both
    gates deny `judge-error` (step 4 cannot list the parent); unfixed: both deny with M-1's kind
    `no-test-resolved` (expected, not yet measured; T0 measures this cell). The kind is the
    discriminating observable.
    (c) control: (a) and (b) under the `step3`-only state — both gates allow, fixed and unfixed.
    Each case asserts its precondition (`os.listdir` of the directory raises `PermissionError`)
    and fails, never skips, when it does not hold (a root uid would not raise).

### FR-4: The Codex gate reads patch headers as Codex does (D2; B6, OD-2)

- **Description**: The Codex gate's `apply_patch` target list (`_targets`, today the `PATCH_TARGET`
  regex) follows codex-cli's header grammar:
  1. The patch is split into lines on `\n` only (not `str.splitlines`, which also splits on VT, FF,
     U+001C–U+001E, U+0085, U+2028, U+2029).
  2. Each line is trimmed at **both** ends with the Unicode `White_Space` set — Python `str.isspace()`
     minus U+001C–U+001F.
  3. A trimmed line that begins with exactly one of `*** Add File: `, `*** Update File: `,
     `*** Delete File: `, `*** Move to: ` (one space after `***`, one after the colon, case as
     written) is a header; the rest of the trimmed line is its path. No other spelling is a header
     (M-22).
  4. A header path that still contains a C0 control byte (U+0000–U+001F) or DEL (U+007F) is
     refused with kind `judge-error` when governed, before any path resolution (M-20: Codex would
     create `src/n.py\x1f`). A header path that is empty after trimming is refused the same way.
     With no governing state the patch is decided as today, the same scope the gate already gives
     an unidentified target.
  5. Every recognised path then goes through FR-1 and FR-2.
  The gate may recognise **more** than Codex (an indented `Move to:`, M-23; a hunk context line
  whose trimmed text is a header): each extra target is governed, never exempted, so the error is
  fail-closed. The `--self-check` verb still prints `CODEX-TDD-GATE: PASS` and additionally checks
  that a trailing-space header and an indented header each yield `src/prod.py`.
- **Acceptance Criteria**:
  - AC-4.1 (D2): M-15 — each trailing variant is its own parametrised case — fixed: deny with M-1's
    kind; unfixed: allow for every variant that leaves a non-`.py` suffix.
  - AC-4.2 (OD-2): M-17 — fixed: deny; unfixed: allow. M-16 — fixed: deny with M-1's kind; unfixed:
    deny "could not identify" (the kind is the observable).
  - AC-4.3: M-19 — fixed: deny; unfixed: allow.
  - AC-4.4: M-20 — fixed: deny `judge-error`; unfixed: allow. A header with an interior U+0001
    (`src/pr\x01od.py`) — fixed: deny `judge-error`; unfixed: deny `no-test-resolved` (read from the
    code: the path keeps its `.py` suffix; the kind is the observable). Under a `step3`-only state
    both cases are allowed, fixed and unfixed.
  - AC-4.5: M-22 spellings, alone in a patch under governing state — deny "could not identify",
    fixed and unfixed (no header recognised).
  - AC-4.6: the trim set is pinned code point by code point: U+0020, U+0009, U+000B, U+000C, U+000D,
    U+0085, U+00A0, U+3000, U+2028 are trimmed; U+001C, U+001F, U+200B, U+FEFF are not (U+001F then
    trips step 4). Each code point is its own case.
  - AC-4.7: `--self-check` exits 0 printing `CODEX-TDD-GATE: PASS`; with the trailing trim removed
    it prints `CODEX-TDD-GATE: FAIL parser`.

### FR-5: The judge bounds its post-kill reap and reports `judge-timeout` (D5; B5)

- **Description**: In `h_mad_tdd_judge._run_bounded`, after `TimeoutExpired` and `os.killpg(…,
  SIGKILL)`, the second wait is bounded by one named module constant `REAP_GRACE_S = 1.0` (seconds;
  plan PD-2, inside this spec's cap 0 < `REAP_GRACE_S` ≤ 2.0 s). If the pipes close within the grace,
  the outcome is today's timeout (kind `timeout`). If they do not — a descendant that left pytest's
  process group still holds stdout or stderr — the runner closes its pipe ends, reaps the killed
  child, and reports a **reap failure**, distinct from a plain timeout. `_run_bounded` returns a
  six-field `NamedTuple`: today's five fields in today's order (`returncode`, `out`, `err`,
  `timed_out`, `error`) plus `reap_failed: bool`; `timed_out` is also true on a reap failure, and
  `error` keeps its one meaning ("Popen raised"). The judge maps a reap failure to DENY kind
  `judge-timeout` on both paths that use the runner (the name map in `resolve`, and pytest in `judge`); `judge-timeout` stops further test
  runs and outranks every other kind in the aggregation (the kind-priority tuple in `judge`).
  `judge-timeout` joins `KINDS`, and the Claude gate's `JUDGE_DENY_RE` alternation, so the Claude
  gate refuses with `BLOCK kind=judge-timeout`; without that edit the same judge line is refused
  `judge-error` ("printed no well-formed verdict line"), which is the observable AC-5.4
  discriminates. The Codex gate passes the kind through its existing `kind={verdict.kind}` reason.
  The detached descendant is not killed (the judge does not know its pid); after the pipes close its
  next write gets EPIPE/SIGPIPE.
- **Worst case**: a governed write returns within `JUDGE_BUDGET_S` (40.0 s) + `REAP_GRACE_S` (1.0 s)
  = 41.0 s + process start-up, instead of waiting for the descendant.
- **Acceptance Criteria**:
  - AC-5.1 (D5): the gap repro — `_run_bounded` with deadline `start + 2.0` on a child that detaches
    `sleep 12` and sleeps 30 — fixed: returns in under `2.0 + REAP_GRACE_S + 1.0` s = 4.0 s and
    reports `reap_failed=True`; unfixed: returns at ≈ 12 s. The test kills the detached sleeper
    through its pidfile in teardown.
  - AC-5.2: a child that times out with no detached descendant still reports a plain timeout
    (`timed_out=True`, `reap_failed=False`); `test_run_bounded_kills_the_process_group`,
    `test_name_map_runs_under_the_budget` and the other existing `timeout` assertions in
    `h-mad/tests/test_h_mad_tdd_judge.py` stay green. Of those tests only
    `test_run_bounded_kills_the_process_group` unpacks `_run_bounded`'s result (five names today);
    its move to the six-field result is a named, reviewed delta. `test_name_map_runs_under_the_budget`
    calls `judge.judge` and does not unpack, so its assertions (kind `timeout`, `< 6.0 s`) are
    unchanged.
  - AC-5.3: `judge()` with the name map replaced by a detaching script, and separately with a fake
    venv interpreter that detaches — each returns DENY `judge-timeout` within `budget_s +
    REAP_GRACE_S + 1.0` s; unfixed: `timeout` after the descendant exits.
  - AC-5.4: Claude gate end to end with a judge stub printing `TDD-JUDGE: DENY kind=judge-timeout
    reason=r` rc 0 — fixed: `BLOCK kind=judge-timeout`; unfixed: `BLOCK kind=judge-error`. Codex gate:
    the reason contains `kind=judge-timeout`.
  - AC-5.5: `judge-timeout` is added as a parametrised row to `test_claude_gate_kind`
    (`h-mad/tests/test_h_mad_tdd_gate_judge.py`) and `test_codex_gate_kind`
    (`h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`).

### FR-6: Pinned repros and a cross-gate differential (B7, OD-5)

- **Description**: Every gap-report repro is a pinned test on the gate(s) it names: D1 on both, D2 on
  the Codex gate, D3 on the Claude gate (and in the differential), D4 on both, D5 on the judge and
  on both gates' kind handling. A **shared differential** runs the same fixtures and spellings
  through both gates and asserts equal decisions:
  - **Domain**: absolute Write spellings that are **in-root**, over a readable chain, in two state
    modes: governing `step5` with `codex_status: exhausted`, and a `step3`-only file. "In-root" is
    decided without needing a canonical target that FR-3 does not produce:
    - a **resolvable** spelling is in-root when its canonical target (FR-1) is inside the canonical
      root;
    - an **unresolvable** spelling (FR-3, either arm) is in-root when its **resolved prefix** is
      inside the canonical root. The resolved prefix is the longest prefix of the spelled
      components, after FR-1 step 1, that FR-1 step 2 walks before FR-3's predicate holds. Every
      component of that prefix exists, resolves, and can be opened, so FR-1 step 3 gives it a
      canonical form. "Inside" includes equal to the canonical root.
    For an in-root unresolvable spelling, both gates must agree on the decision and, when both
    deny, on the kind. FR-3 fires at step 2, before step 6's inside-root test, so the expected
    result is `judge-error` under the governing state and allow under the `step3`-only state. The
    resolved prefix of each required unresolvable cell is inside the canonical root: `R/docs` for
    M-12, `R/src` for M-13's leaf case and for M-14, and `R` for M-13's intermediate case
    (`lnk -> nowhere`). The same holds for each of them under M-18. So no required cell falls
    outside the domain. Cells: M-1…M-14 and M-18, plus the controls `notes.md`, `tests/test_x.py`
    and `sub/test_x.PY`.
  - **Assertions**: the two decisions are equal on every cell; on every cell where both deny, the
    kinds are equal (the Codex kind is parsed from `kind=([a-z-]+)` in the reason); each cell's
    decision, and its kind when it denies, equals its row in a published expectation table in the
    test, whose deny count is
    derived by the test from the table, never typed.
  - The differential lives in `h-mad/tests/` and reuses `tdd_gate_support.decision` and
    `hermetic_env`. It does not replace `test_dd7_differential_matches_the_published_cells`, which
    must keep its 126 cells and 18 denies (none of its cells contains a symlink or a case variant).
- **Acceptance Criteria**:
  - AC-6.1: the differential passes on the fixed tree. On the unfixed tree its gate-equality
    assertion fails on exactly M-4, M-5, M-6, M-7, M-8, M-11 and M-12 (the cells where the gates
    disagree today, per §"Measured premises"), and its expectation-table assertion additionally
    fails on M-2, M-3, M-9, M-10, M-13 and M-14 — run, not asserted. M-18's M-14 cell additionally
    fails both assertions on the unfixed tree (Claude allows, Codex denies `judge-error`; v1.6, D-4).
  - AC-6.2: removing FR-1 from either gate alone makes the differential fail (run once per gate).
  - AC-6.3: `docs/03-analysis/probes/codex-tdd-gate-defects/dd7_differential.py` re-run on the fixed
    tree reproduces its published cells; any changed cell is a stated, reviewed delta.

### FR-7: Every guard bites

- **Description**: Each guard this feature adds is mutation-tested with the bundled 5e harness,
  scored on the pytest summary, one mutation per guard and one per branch of an alternation, each
  branch mutated alone.
- **Acceptance Criteria**:
  - AC-7.1: deleting or negating each of these turns at least one named AC red: the Claude-gate
    canonicaliser (AC-1.1), the Codex-gate canonicaliser (AC-1.4), the on-disk-spelling step (AC-1.5),
    the hard-link rule (AC-1.9), the root canonicalisation (AC-1.3), the fold in each gate (AC-2.2),
    the dangling branch and the loop branch of FR-3's predicate (AC-3.1, AC-3.2; separate
    mutations), FR-3's cannot-be-read arm (AC-3.6), the governing-state condition of FR-3
    (AC-3.3), the leading trim and the trailing
    trim (AC-4.2, AC-4.1; separate mutations), the control-byte refusal (AC-4.4), the `\n`-only split
    (AC-4.6), the bounded reap (AC-5.1), the reap-failure → `judge-timeout` mapping on the name-map
    path and on the pytest path (AC-5.3; separate mutations), the priority of `judge-timeout`
    (AC-5.3), the `JUDGE_DENY_RE` branch for `judge-timeout` (AC-5.4), the
    `h_mad_resume_decision.py` entry in `SAFE_HMAD_SCRIPT_OPTIONS` (AC-8.1), that entry's equality
    with the parser's options, mutated by adding one option to the entry (AC-8.2), the id-file read
    behind `--session-id-from-git-dir` (AC-8.3), its `cannot_judge` answer when the id cannot be
    read (AC-8.4), and the mutual exclusion of `--session-id` with `--session-id-from-git-dir`
    (AC-8.5).

### FR-8: The Codex gate admits the documented resume oracle (OD-6)

- **Description**: A Codex-hosted `/h-mad` must be able to run the resume oracle in its documented
  form while any feature on the state chain is in `step5`. There are three changes.
  1. **Safe list.** `SAFE_HMAD_SCRIPT_OPTIONS` in `h-mad/hooks/h-mad-codex-tdd-gate.py` gains the
     key `h_mad_resume_decision.py`. Its value is exactly the set of long options that the
     script's own argparse parser declares, minus `--help`. After change 2 that is `--feature`,
     `--host`, `--now`, `--session-id`, `--session-id-from-git-dir` and `--state`: six options,
     counted from the `add_argument` calls in `main()` plus the new one. `_safe_hmad_script` gains
     no per-script value check for this key, and it falls through to its closing `return True`.
     The script is read-only: `decide` only reads the state file, and change 2 adds only a
     `git rev-parse` call. The lexical subset `SIMPLE_SHELL_COMMAND`, the trusted-executable rule,
     and the `scripts_root` containment of the script path are unchanged. So `$`, `~` and command
     substitution stay refused, and the script path stays a literal absolute path, as each
     adapter's §"Context budget and claims" already requires.
  2. **Session id with no command substitution.** This is a **code change** to
     `h-mad/scripts/h_mad_resume_decision.py`. It adds a boolean flag, `--session-id-from-git-dir`,
     in one argparse mutually exclusive group with `--session-id`. With the flag, the script runs
     `git rev-parse --absolute-git-dir` in its own working directory under a bound of 10 s. It
     reads `<git dir>/h-mad-session-id.<feature>`, where `<feature>` is the `--feature` value, and
     takes the stripped content as the session id. It then decides exactly as
     `--session-id <that id>` would.
     - **Failure modes.** Each of these makes the script print `cannot_judge`, whatever `--host`
       says: `git` absent from `PATH`; a non-zero `git` exit, which includes a working directory
       outside any repository; the bound expiring; the id file absent; the id file unreadable
       (`OSError`); and an id that is empty after stripping. The flag asked for an id, and
       "could not read it" is not "no id given". The token keeps its one documented meaning: the
       oracle could not judge.
     - **Usage errors.** Passing both `--session-id` and `--session-id-from-git-dir` is an argparse
       error: exit 2, empty stdout, and `not allowed with argument` on stderr. Callers read the
       stdout token, never `$?`, and an empty stdout is "no decision", so they halt.
     - **Why this form.** An environment-variable prefix fails the gate: an `argv[0]` containing
       `=` is refused. A file-path flag would need the literal git-dir path. `git rev-parse` is
       itself refused under `step5` (§"Measured premises"), so a session resuming mid-`step5`
       could not derive that path through the gate. A literal uuid pasted as `--session-id`
       passes the gate, but it moves the minted file's value through the agent's own
       transcription. The script-side read removes both of these.
  3. **Adapters.** The fenced resume-oracle line under §"Context budget and claims" in
     `h-mad/references/codex-runtime.md`, `grok-runtime.md` and `agy-runtime.md` becomes
     `python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_resume_decision.py" --host <host> --state
     docs/.bkit-memory.json --feature "<feature>" --session-id-from-git-dir`. `<host>` stays as
     each adapter spells it today (`codex`, `grok`, `agy`). agy does not run the Codex gate. It
     changes too because `h-mad/tests/test_host_runtime_docs.py` pins one oracle form across all
     three adapters (`HOST_ADAPTERS`). The adapters describe an unreadable id file as giving the
     oracle an empty id. That prose becomes "the oracle cannot read the id and returns
     `cannot_judge`". codex and agy spell it "the oracle receives an empty id and returns
     `cannot_judge`". grok spells it "An unreadable id file gives the oracle an empty id and
     `cannot_judge`". The mint line and the `h_mad_state_write.py` lines are unchanged (see
     Residuals). The Claude-host line in `h-mad/SKILL.md` (`--session-id "<this session's id>"`) is
     unchanged, because the Claude gate does not police shell commands.
- **Acceptance Criteria** (a governing `step5` state unless stated; "fixed"/"unfixed" name the
  observable that differs):
  - AC-8.1 (gate admits the oracle). This runs end to end through the Codex gate, with the
    shell payload shape of `test_codex_hook_allows_exact_safe_hmad_control_script`
    (`h-mad/tests/test_h_mad_codex_runtime.py`). The command is each adapter's oracle line, taken
    from the adapter file, with `<HMAD_SKILL_ROOT>` replaced by the literal absolute skill root and
    `<feature>` by a literal name. Fixed: allow (rc 0, empty stdout). Unfixed: deny, with the reason
    beginning "H-MAD Phase 5 permits only explicit test, read-only, and H-MAD control commands".
    The same pair holds for the literal form `--session-id <uuid>`. Control: the pre-FR-8
    `--session-id "$(cat …)"` line is denied fixed and unfixed (the lexical subset did not loosen).
  - AC-8.2 (exact options). A test derives the long options of `h_mad_resume_decision.py`'s parser,
    minus `--help`, and asserts that they equal the safe-list entry. The test never types the set.
    Fixed: equal. Unfixed: the entry is absent. Under governing state, a command carrying
    `--bogus x` and one carrying `-h` are each denied, fixed and unfixed.
  - AC-8.3 (the flag reads the minted id). Each case is its own: a git repository, and a linked
    worktree whose git dir is not `<root>/.git`. The id is minted exactly as the adapter's mint
    line writes it (a trailing newline included). The state holds the feature with
    `last_completed_phase` 4. First, with it owned by the minted id, `--host codex
    --session-id-from-git-dir` prints `enter_autonomous`. Second, with it owned by another session
    that is live under `--now`, the same command prints `owned_elsewhere`. Each token equals what
    `--session-id <file content>` prints. Unfixed: exit 2 with `unrecognized arguments`, empty
    stdout.
  - AC-8.4 (fail-closed). Each failure mode of change 2 is its own case, each under
    `--host codex` and under `--host claude`, and each prints `cannot_judge`. The cases: id file
    absent; empty; whitespace-only; mode 000 (the case asserts that reading raises
    `PermissionError`, and it fails, never skips, when that does not hold); working directory
    outside any repository; `git` absent from a hermetic `PATH`. The `--host claude` case
    discriminates. Without the flag's own fail-closed branch, a missing id reaches `decide` as
    `None`, and on the Claude host that is not `cannot_judge`: it prints `enter_autonomous`
    against the AC-8.3 state. Unfixed: exit 2, empty stdout.
  - AC-8.5 (mutual exclusion). Both `--session-id x` and `--session-id-from-git-dir` give exit 2,
    empty stdout, and stderr containing `not allowed with argument`. Unfixed: exit 2 with
    `unrecognized arguments` instead.
  - AC-8.6 (adapters). Each of the three adapters' fenced oracle line contains
    `--session-id-from-git-dir`, and no `$`. `test_host_runtime_docs.py` changes in two named,
    reviewed deltas. First, the `oracle` condition of `test_claims_section_fenced_lines` moves
    from `"--session-id " + SID_READ` to the new flag. Second, `test_claims_lines_execute_across_invocations`
    selects the oracle line by the new flag, and its oracle run still returns the minted owner's
    token. Its other cases (`create-claim`, `claim`, `beat`, `set`, `release`, `mint`,
    `oracle-first`, `no-dollar-sid`) are unchanged and stay green. Fixed: AC-8.1 passes on the
    line the adapter carries. Unfixed: the line contains `$(`.

## Contract: tokens and kinds the gates emit

- **Claude gate** (form b, `readonly REFUSAL_FORM=b`): allow = rc 0 and empty stdout; deny = rc 0 and
  one JSON object whose `permissionDecisionReason` begins `[H-MAD-TDD-GATE] BLOCK kind=<K>:`. `K` is
  one of the judge kinds `no-test-resolved`, `test-missing`, `venv-escapes-root`, `pytest-missing`,
  `pytest-error`, `no-tests-ran`, `no-summary`, `test-passing`, `timeout`, **`judge-timeout`**
  (new), `judge-error`, or a gate kind `codex-authorship`, `fallback-grok`, `fallback-invalid`,
  `judge-error`. Any other stdout, or a non-zero rc, is a malformed decision; the caller reads the
  kind token, never `$?`.
- **Codex gate**: allow = rc 0 and empty stdout; deny = rc 0 and one JSON deny. Judge-path denies
  carry `kind=<K>` with `K` from the judge list above; FR-3 and FR-4 denies carry
  `kind=judge-error`. The existing kind-less denials (unreadable state for a shell command, shell
  policy, "could not identify this write target", "outside or unreadable") are unchanged.
- **Judge**: `TDD-JUDGE: DENY kind=judge-timeout reason=<text>` is a new well-formed line; `KINDS`
  gains `judge-timeout`, so it has 12 members (count of the frozenset literal after the edit).
  `judge-timeout` means "the runner could not reap the test process's pipes within the grace"; the
  caller refuses the write and reports it separately from a slow test (`timeout`).
- **Resume oracle** (`h_mad_resume_decision.py`, FR-8). The script prints exactly one of the tokens
  in its docstring: `start_fresh`, `resume_manual`, `enter_autonomous`, `halted`, `complete`,
  `owned_elsewhere`, `cannot_judge`. FR-8 adds no token. `cannot_judge` gains six causes, the
  failure modes of `--session-id-from-git-dir`, and each means "could not judge; do not initialise
  or claim". An argparse usage error gives an empty stdout, rc 2, and a message on stderr: an
  unknown option, a missing `--state`/`--feature`, or `--session-id` together with
  `--session-id-from-git-dir`. The caller reads the token and treats an empty stdout as no
  decision (halt). It never reads `$?`. Under a governing `step5` state, the Codex gate either
  allows the oracle command (rc 0, empty stdout) or denies it with the kind-less shell-policy
  reason.

## Non-Functional Requirements

- **Performance**: FR-1 adds at most one Python call to the Claude gate (it already runs one at
  `# M:H11`) and one directory listing per existing leaf. FR-5 adds at most `REAP_GRACE_S` to a
  timed-out judge.
- **Security**: a workflow guard, not a sandbox (`h-mad/references/codex-runtime.md` §"Trust
  boundary"). No environment variable is added. FR-8 adds one CLI flag,
  `--session-id-from-git-dir`, to `h_mad_resume_decision.py`. It also admits that one read-only
  script to the Codex gate's shell allow-list, and it adds no value check.
- **Compatibility**: every existing test in `h-mad/tests` passes, apart from the deltas named in
  AC-5.2, AC-5.5 and AC-8.6 and the verdict changes FR-1 lists. The Codex gate's `--self-check` prints
  `CODEX-TDD-GATE: PASS`.

## Residuals (stated exactly)

- **Hard links across directories.** The gates decide on a path, not an inode. A production file
  hard-linked into `tests/` is exempt when written through the `tests/` name. FR-1 step 4 covers
  links inside one directory only.
- **Writers that replace a leaf symlink instead of following it.** FR-1 decides a leaf symlink by
  its referent, which is what Codex `apply_patch` does (measured). Claude Code's Write and Edit
  refused a leaf symlink (Edit measured on 2.1.284, 2026-09-29). Residual: MultiEdit and
  NotebookEdit are absent from that build and unmeasured; any Claude Code build, or any other
  writer, that **replaces** a leaf symlink with a regular file writes at the link location while
  FR-1 decides by the referent, and a production link into `tests/` would then be a fail-open. A
  tool that appears in a later build is measured before it is trusted here.
- **A legitimate `*.PY` (any case) data file** outside the exempt directories is refused while
  governed (B3).
- **Case-variant exempt spellings are governed**: `FIXTURES/…` with on-disk `fixtures/` becomes
  allowed (M-10), but `TESTS/x.py` for a directory that does **not** exist is a new directory named
  `TESTS` and is governed.
- **Filesystems without an on-disk-spelling primitive** (Linux `casefold` ext4, where `F_GETPATH` is
  absent): FR-1 step 3 falls back to a spelling-preserving resolution, and M-8/M-9-class spellings
  remain open there. The measured platform is macOS APFS only.
- **Permission-denied components**, split by what the gate can do to the component:
  - a component the gate cannot `lstat` (its parent lacks `x`) is treated as absent. The gate runs
    as the writer's uid, so the writer cannot traverse it either and the write fails; the verdict is
    inert.
  - a component the gate can `lstat` but the on-disk-spelling primitive cannot open or list (e.g.
    mode 0311, or a leaf parent without `r`) is **not** a residual: it is FR-3's second arm
    (refused `judge-error` when governed, allowed otherwise).
  - what remains open: a writer running under a different uid from the gate, or with privileges
    the gate lacks, can reach a component the gate cannot; the gate reads only its own
    permissions.
- **Divergences excluded from the differential (OD-5)**: an exempt write on an unreadable chain
  (Claude allows, Codex refuses — predecessor OD-A); an outside-root target (Codex refuses every
  file type when governed, Claude governs only `.py`); relative targets (Claude joins the root,
  Codex the payload `cwd`).
- **Unresolvable spellings outside the differential's domain (FR-6)**. The first is an
  unresolvable spelling whose resolved prefix is outside the canonical root, such as a dangling
  link under an outside-root directory. It belongs to the outside-root divergence class above:
  Claude reads the target's own chain, and Codex reads `_any_phase5_status(root)`. The second is a
  root that is itself unresolvable, which has no canonical root, so every spelling under it is
  outside the domain. No required cell is in either category. The differential makes no claim
  that the gates agree on these spellings.
- **The detached descendant keeps running** after a reap failure (FR-5).
- **Host hook timeouts** are not measured (predecessor OQ-D1); FR-5 bounds the judge, not the host.
- **Over-recognised Codex headers** (M-23, trimmed hunk lines) are governed; a false refusal is
  possible there.
- **FR-8 closes the oracle line only.** Each adapter's §"Context budget and claims" still documents
  five `h_mad_state_write.py` lines: `--create --claim`, `--claim`, `--beat`, `--set` and
  `--release`. They use `"$HMAD_SKILL_ROOT/…"` and `"$(cat …)"`, and `$` is outside
  `SIMPLE_SHELL_COMMAND`'s class (read from the code at `78e35abf`). So the Codex gate still
  refuses them under a governing `step5` state. That covers a heartbeat (`--beat`) or a release
  during Phase 5. FR-8 does not change them. The operator's fold decision names the resume
  oracle. Closing them is a separate decision.
- **Paths outside the lexical subset.** A skill-root path containing a character outside
  `SIMPLE_SHELL_COMMAND`'s class cannot be passed to the oracle under a governing state, for
  example `~`, `$`, `(`, `;` or a non-ASCII letter. This is true of every script on the safe
  list today.
- **Unreadable state.** When `_any_phase5_status` is `unknown`, the Codex gate refuses every shell
  command ("H-MAD state is unreadable; refusing shell execution fail-closed."), and the oracle is
  refused with them. That is unchanged. The oracle's own answer on an unreadable state file would
  be `cannot_judge`.

## Out-of-Scope

- The shell-command policy and the Codex `workdir` question (gap report §"Unverified").
- The empty-target rule under a governed sub-project (gap report §"Unverified").
- The name map (`h_mad_derive_test_path.sh`) and impl-plan test resolution.

## Assumptions

- APFS on the measuring machine is case-insensitive and normalisation-insensitive (the default).
  AC-1.10 turns this into a checked precondition.
- Codex's `apply_patch` grammar is as measured on codex-cli 0.158.0; a later Codex that trims
  differently is caught only if the **manual** Codex-grammar reading (plan R-4) is re-taken by hand against the new binary. AC-4.6 pins the gate against the
  grammar as measured on 0.158.0; no committed probe or test invokes `codex` (plan PD-4), so
  nothing committed detects the change.

## Open Questions

- None open on OD-1…OD-5: all five were operator-approved on 2026-09-29 (commit `662b1ce1`; see the
  table above).
- Plan v1.0's OQ-P1 is decided (operator, 2026-09-29: refuse) and folded into FR-3's second arm
  and AC-3.6. Plan PD-5's measurement is taken (Edit refused on Claude Code 2.1.284); FR-1's leaf
  rule is unamended.
- OD-6 is decided (operator, 2026-09-29: fold the Codex resume denial into this feature) and is
  specified as FR-8.

## Version History
- v1.0: Initial specification draft (2026-09-29) from brainstorm v1.1 (c83c62fe) and operator decisions B1-B7. FR-1 one target-normalisation rule (D3, D4), FR-2 .py fold (D1), FR-3 unresolvable target refused judge-error when governed (OQ1), FR-4 Codex header grammar (D2), FR-5 bounded reap + judge-timeout (D5, OQ2), FR-6 pinned repros + cross-gate differential, FR-7 mutation. OD-1..OD-5 raised from measurements at 1a77e1c4 / codex-cli 0.158.0 (on-disk spelling, leading-whitespace headers, fold before name tests, governed-only refusal, differential domain); each owes operator confirmation.
- v1.1: Revision (2026-09-29) answering plan v1.0 (f5e44a50) owed items and operator decisions. OQ-P1 decided refuse: FR-3 gains a second arm (an existing root/target component the on-disk-spelling primitive cannot open or list is unresolvable; judge-error when governed, allow otherwise; never fall back to the spelling), FR-1 step 3 cross-reference, AC-3.6 (a/b/c), AC-7.1 mutation row, permission residual split; 0311 reading measured at f5e44a50. PD-5 recorded as a measured premise: Edit on a leaf symlink refused on Claude Code 2.1.284, MultiEdit/NotebookEdit absent from that build (unmeasurable), FR-1 leaf rule unamended; not re-derivable by T0's probe. PD-2 applied to FR-5: REAP_GRACE_S = 1.0 s, six-field NamedTuple adding reap_failed, AC-5.1 bound 4.0 s, worst case 41.0 s. AC-5.2 corrected: only test_run_bounded_kills_the_process_group unpacks _run_bounded. PD-4: table stays until T0's committed reading replaces it.
- v1.2: OD status (2026-09-29): OD-1..OD-5 recorded as operator-approved 2026-09-29 (662b1ce1) in the Binding-decisions preamble and Open Questions; 'open decision' renamed 'operator decision'. No requirement changed.
- v1.3: Revision (2026-09-29) applying plan v1.2 (4192ad8c) owed items under plan PD-4 (no committed probe or test invokes codex). Assumptions: a later Codex that trims differently is caught only if the manual R-4 reading is re-taken against the new binary. Measured premises: the Codex-writes column, the trim set and the leaf-symlink writer rows are manual R-4/R-5 readings, and the tables are replaced by a pointer to T0's unfixed reading together with its manual R-4 and R-5 rows; OQ-P1 cell wording unchanged (gate-side). FR-1 gains AC-1.11, the outside-root symlink control of the M:H20 raw-spelling conjunct (plan R-3): fixed and unfixed both deny no-test-resolved, the H20B mutant must turn the fixed gate to allow, and H20B does not move the cell on the unfixed tree (measured at 4192ad8c). AC-7.1 unchanged.
- v1.4: Corrective revision (2026-09-29) answering plan audit cycle 2 (codex must #2) and operator decision OD-6. FR-6/OD-5: differential-domain membership defined for unresolvable targets: in-root when the resolved prefix (longest spelled prefix FR-1 step 2 walks before FR-3's predicate holds) is inside the canonical root; both gates agree on decision and kind; M-12-M-14 and M-18 in domain; out-of-domain unresolvable spellings listed under Residuals. OD-6 (operator 2026-09-29, fold the carried Codex resume denial): new FR-8 with AC-8.1-AC-8.6: SAFE_HMAD_SCRIPT_OPTIONS admits h_mad_resume_decision.py with exactly its parser's long options minus --help (six); code change adds --session-id-from-git-dir (script reads <git dir>/h-mad-session-id.<feature>; every read failure prints cannot_judge; exclusive with --session-id); the three adapters' oracle line moves to that form (test_host_runtime_docs deltas named). AC-7.1 gains five FR-8 mutation rows (T8 floor 20 -> 25). Measured premise for FR-8 at 78e35abf; Contract, NFR, Residuals, Open Questions updated.
- v1.5: Operator decision (2026-09-30): FR-1 'Verdict changes toward ALLOW' gains the Codex-gate key cell=M-18 M-14 state=step3, deny judge-error -> allow, approved (unfixed reading reading-unfixed.txt at a737962a: Codex deny judge-error, Claude allow; step3 is ungoverned). The approved deny-to-allow set is now 7 keys (design table's 6 plus this one); this spec states no count of that set. No other requirement changed; the M-18 table row, AC-3.3 and AC-6.1 still state the unfixed Codex M-14 cell as allow and are left for a separate decision.
- v1.6: Operator decisions (2026-09-30, post-merge; report §"Carry Items" at 8d9c9047). D-1: FR-3 states the design v1.4 root-refuse for a root that cannot be entered, on both gates. D-2/D-3: that refuse is spelling-independent and Codex now matches it. N-1: `..` out of a non-symlink directory is lexical, not an arm-2 site. D-4: the M-18 row, AC-3.3 and AC-6.1 now state the unfixed Codex M-14 cell as deny `judge-error`.
