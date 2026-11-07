# Change review — round 5, the delta: working tree against HEAD de7d16ff (quickfix-r5.diff) — GATING

Rubric, narrowed by the dispatch:
- Does `isprintable()` close every separator `splitlines()` honours and every control character, without falsely refusing a ref users really write?
- Is `shlex.quote` safe and accurate in the hint?
- Does the filed candidate row describe the class correctly?

## Evidence
- read: 3 files, about 40 lines.
  - The round-4 → round-5 delta. `git diff` is byte-identical to quickfix-r5.diff.
  - `h_mad_assemble_tdd.py` 63-69 (imports), 842, 862, 1183-1186, and the four detail `print` lines by grep.
  - `docs/skill-candidates.md` 3034.
- ran: 5 commands. Scratch tree from `git archive` plus `git apply quickfix-r5.diff`, `cmp`-equal to the working tree, now deleted.
- tests run (python3.11, scratch): `test_a_base_ref_with_a_line_break_halts_and_forges_no_token_line` (7 cases) and `test_a_base_ref_name_with_a_line_break_is_refused_on_every_route`: 15 passed. Hand mutant `if False:  # M:RV-BASE-LINE` against `[line-separator]`: killed, with `HALT diff_path_invalid` and the raw separator printed inside the quoted ref.

Checked and correct:
- `isprintable()` closes the whole class. I enumerated all 0x110000 code points on both 3.15.2 and 3.11.8. The characters `splitlines()` breaks on are `0xa 0xb 0xc 0xd 0x1c 0x1d 0x1e 0x85 0x2028 0x2029`; every one is non-printable, and so is every `Cc` control character. `\x1d`, `\x1e` and ` ` are covered although the test does not list them.
- Refs people write are accepted: `기능/한글`, `é`, decomposed `é`, `feature/ünïcödé`, `日本語`, `emoji-🚀`, `HEAD@{2 days ago}` and `:/fix the bug` (ASCII space is printable), `origin/main`, `v1.0^{}`, `HEAD~1`, `@{upstream}`.
- `shlex.quote` is accurate and safe there. `HEAD` stays `HEAD`, which keeps the test's expected substring. `HEAD@{2 days ago}` becomes `'HEAD@{2 days ago}'`. `:/it's` becomes `':/it'"'"'s'`, which can be pasted into a shell as is. It wraps the value and does not escape it, so its safety depends entirely on the `isprintable()` check above it. The mutant shows the separator surviving inside the quotes once that check is gone. With the check in place it cannot carry a line break.

## Must-fix
None

## Should-fix
- The filed row overstates its remedy and leaves part of the class out. It says "One escape at the single detail printer would close the class". The script has four detail printers:
  - 1185 `print(f"  {halt[1]}")` (flag names only, safe today);
  - 1204 `print(f"  {check_line}")`;
  - 1260 `print(f"  {exc.detail}")`;
  - 1267 `print(f"  {prompt}: {exc}")`.

  `--prompt`, which the row lists, reaches the output through 1267 and the PASS line, not through `exc.detail`, so escaping at 1260 alone does not cover it. The row also omits `--feature`: it is raw in `[H-MAD] {args.feature} tdd-assemble halt … {args.task}`, and it reaches `impl_plan_unreadable` when `--impl-plan` is not given. Suggested rewording: "every value printed to stdout (the HALT details at 1260/1267, the PASS line, the `[H-MAD]` marker) goes through one escaper".
  quote: docs/skill-candidates.md:3034 › `One escape at the single detail printer would close the class`

## Nit
- `isprintable()` also refuses valid but unusual refs: a branch name with a ZWJ emoji sequence (`family-👨‍👩‍👧`), NBSP, a zero-width space, or a bidi override (`‮`). The refusal fails closed and `--diff-path` is the way around it. Refusing bidi controls is arguably a benefit. One clause in the halt message or docstring ("format and space characters other than ASCII space are refused too") would stop it reading as a bug.
