# Design: gate-non-py-production-files

## Executive Summary
All three Phase-5 write gates (Claude, codex and agy) judge a listed code-like non-`.py` file through one listing function in the judge, `h_mad_tdd_judge.listing`. They allow doc/data files through one predicate in `h_mad_target_identity`, `is_doc_data`. The Claude gate reaches both through processes it already starts or one new merged verb, so an unlisted code-like write costs it two extra Python processes where state exists.

## Overview
The spec (v1.10) and the plan (v1.6) fix the rule. This design names each mechanism the plan left open:
- **D4. The listing decision.** It has a single home, `h_mad_tdd_judge._match_plans`. `resolve` and the new `listing` function both consume it. The Claude-facing CLI verb is `listing`, which prints one `TDD-LISTING:` line.
- **D13. The doc/data definition.** It lives in `h_mad_target_identity`. The Claude gate **uses** it rather than holding a bash copy: the canonicalise process the gate already runs (marker `# M:H11`) prints one extra line. This settles R11, R12 and R13 by construction. It is also the only option under which spec AC-11.6's first sentence holds on the Claude host (§"D13 decision").
- **D7 and D8. The new call sites.** codex and agy each get one new call site on the code-like path, after their `if not production:` guard.
- **D12 and D14. The FR-9 proof.** A committed probe drives the hooks hermetically, both the worktree hooks and the base-commit hooks.

Constraints: macOS `/bin/bash` 3.2 for the Claude gate, stdlib-only Python, and `.py` behaviour unchanged on every existing test.

## Architecture Overview
```
             canonical names (h_mad_target_identity.canonicalise)
                               |
          +--------------------+---------------------+
          | is_doc_data(names)  (D13, one definition)|  -> ALLOW, before any state read
          +--------------------+---------------------+
                               | not doc/data
            any production-.py name? --yes--> existing .py path (unchanged)
                               | no
            exempt location?  --yes--> ALLOW (unchanged rules)
                               | no
            read_chain -> none: ALLOW | unreadable: DENY judge-error
                               | active
            h_mad_tdd_judge.listing(root, names, records)   (D4, one function)
                 not-listed: ALLOW | unreadable: DENY judge-error
                               | listed (selected = least listed basename)
            [Claude only: existing implementer / peer / fallback refusals]
            h_mad_tdd_judge.judge(root, selected, records) -> verdict
```
Transport per host:
- **codex.** In-process, through `_load_judge()`, which the module already imports from `h_mad_target_identity`.
- **agy.** In-process, through the `judge` name that `main` binds with `import h_mad_tdd_judge as judge`.
- **Claude.** Through `python3 "$JUDGE" listing …`, one process that reads the chain and decides listing. The doc/data predicate rides the `# M:H11` canonicalise process, which already exists.

`listing` lives in the judge, and every host calls it: codex and agy in-process, Claude through the verb. `listing` and `resolve` share `_match_plans`, so the comparison `os.path.realpath(base / entry) == str(real_target)` exists exactly once (spec FR-3 "No gate re-implements the match").

## Detailed Design

### Tree premises this design rests on (re-run at `3ff9ea4a`, from PROJECT_ROOT)
Each premise below gives its command and the output it printed. Each multi-line block is fed to `/bin/bash -s` from PROJECT_ROOT. A block writes only under `mktemp -d` directories and deletes them.
- **The judge's match lives in `resolve`.** Command: `grep -n 'for entry in task\["production"\]' h-mad/scripts/h_mad_tdd_judge.py`. Output: one matching line, inside `resolve`. `resolve` notes an unreadable impl-plan as `"<plan>: impl-plan unreadable: <Exc>"` and continues, so `resolve` alone cannot tell "unreadable" apart from "not listed".
- **The Claude gate starts two Python processes before any doc/data decision.** Command: `grep -n 'python3' h-mad/hooks/h-mad-tdd-gate.sh | grep -v '~/.claude'`, which drops the refusal-message lines that only name a command. Output: 5 matching lines, one per launch site. They are the stdin reader (`TP=$(python3 -c "$READER")`) and the canonicalise call (`# M:H11`), then `_find_judge` (`# M:W6`), the `state` verb (`# M:W5B`) and the `judge` verb (`# M:W2`).
- **Canonical names come sorted, and a directory has none.** Run on an APFS volume:

  ```bash
  R=$(cd "$(mktemp -d)" && pwd -P); git -C "$R" init -q; mkdir "$R/scripts"; : > "$R/scripts/tool.sh"
  ln "$R/scripts/tool.sh" "$R/scripts/hard.sh"; ln -s scripts/tool.sh "$R/link.sh"; : > "$R/CHANGES.MD"
  python3 - "$PWD" "$R" <<'PY'
  import sys
  sys.path.insert(0, sys.argv[1] + "/h-mad/scripts")
  from h_mad_target_identity import canonicalise
  root = sys.argv[2]
  for t in ("scripts/tool.sh", "scripts/TOOL.SH", "link.sh", "changes.md", "scripts/New.SH", "scripts"):
      i = canonicalise(root, root + "/" + t, root)
      print(f"{t!r}: target={i.target[len(root):]} names={i.names}")
  PY
  rm -rf "$R"
  ```

  Output:

  ```text
  'scripts/tool.sh': target=/scripts/hard.sh names=('hard.sh', 'tool.sh')
  'scripts/TOOL.SH': target=/scripts/hard.sh names=('hard.sh', 'tool.sh')
  'link.sh': target=/scripts/hard.sh names=('hard.sh', 'tool.sh')
  'changes.md': target=/CHANGES.MD names=('CHANGES.MD',)
  'scripts/New.SH': target=/scripts/New.SH names=('New.SH',)
  'scripts': target=/scripts names=()
  ```

  So `Identity.target` is the least name, and a directory target has no names.
- **Stub trees replace the identity module.** Command: `git grep -n 'def emit_canon' -- h-mad/tests`. Output: two stub `h_mad_target_identity.py` modules, both written by `h-mad/tests/test_h_mad_tdd_gate_judge.py` (the `_tree_b` helper, and one CANON-variant test). Both define only `canonicalise` and `emit_canon`.
- **Which existing mutants anchor the lines this feature edits.** A scan of every spec's `find`:

  ```bash
  python3 - <<'PY'
  import glob, json, os
  NEEDLES = ("M:H11", "                production = []", "tasks = _parse_tasks(text)  # M:W3",
             "ungated", "_NON_PY_PATH_RE = ", 'if not token.endswith(".py"))')
  for path in sorted(glob.glob("h-mad/tests/mutation-specs/*.json")):
      spec = json.load(open(path, encoding="utf-8"))
      entries = spec if isinstance(spec, list) else spec.get("mutations", [])
      for m in entries:
          hits = [n for n in NEEDLES if n in m.get("find", "")]
          if hits:
              print(os.path.basename(path), (m.get("id") or m.get("name"))[:32], hits, "symbol=%s" % m.get("symbol"))
  PY
  ```

  Output:

  ```text
  agy_tdd_gate.json fr4-t6-t7-skipped-when-inactive ['                production = []'] symbol=main
  claude_gate_judge_wiring.json H11 ['M:H11'] symbol=None
  claude_gate_judge_wiring.json CG-CANON ['M:H11'] symbol=None
  tdd_judge_wiring.json W3R ['tasks = _parse_tasks(text)  # M:W3'] symbol=None
  tdd_judge_wiring.json W3F ['tasks = _parse_tasks(text)  # M:W3'] symbol=None
  wire_pin_ungated.json U1: NON-PY PATHS NEVER COLLECTED ['ungated'] symbol=None
  wire_pin_ungated.json U2: EXTENSION REQUIRED. `h-mad/b ['_NON_PY_PATH_RE = '] symbol=None
  wire_pin_ungated.json U3: PYTHON REPORTED TOO. Every ` ['if not token.endswith(".py"))'] symbol=None
  wire_pin_ungated.json U4: UNSHAPED PLAN DROPS THE KEY. ['ungated'] symbol=None
  wire_pin_ungated.json U5: COMPUTED, NEVER PRINTED. The ['ungated'] symbol=None
  ```

  That is 10 mutants: 2 on `# M:H11`, 1 on agy's `production = []`, 2 on `# M:W3`, and all 5 of `wire_pin_ungated.json`. U1, U4 and U5 name `ungated` literally, U2 anchors the regex and U3 anchors the extend's `if not token.endswith` tail. §"FR-1 and FR-2" disposes of all five.
- **The mutation harness refuses an anchor that does not match exactly once.** Command: read `h_mad_mutation_harness.py` around the comment "The assert-landed guard". Its rule is `hits != 1` → `refused` ("anchor matched N times … expected exactly 1"). An anchor whose `symbol` key no longer matches its enclosing symbol is also refused ("anchor migrated"). A refused mutant is neither caught nor survived.
- **The bash 3.2 constructs (§D13, §Claude gate).**

  ```bash
  echo "$BASH_VERSION"
  R=$(printf 'CANON 1\nf1\ndocdata yes'); echo "last=[${R##*$'\n'}]"; echo "rest=[${R%$'\n'*}]"
  R=single; echo "one-line last=[${R##*$'\n'}] rest=[${R%$'\n'*}]"
  set -u; L=(); count() { echo "argc=$#"; }; count ${L[@]+"${L[@]}"}; L=(--name "a b"); count ${L[@]+"${L[@]}"}
  ```

  Output:

  ```text
  3.2.57(1)-release
  last=[docdata yes]
  rest=[CANON 1
  f1]
  one-line last=[single] rest=[single]
  argc=0
  argc=2
  ```

  So the split yields the last line and the rest, and a one-line value yields itself on both sides, which the strict parse then refuses. The `${a[@]+…}` guard expands nothing for an empty array under `set -u`, and keeps a two-word element pair as two arguments.
- **Who authors on the Claude host.** `resolve_implementer` picks codex for an unset or null `implementer`, then agy, then the fallback. `implementer=null` therefore does not make Claude the author. Claude is the author only with both peers unavailable. The stubs put both CLIs on `PATH`, so the machine's installed tools do not decide the reading. The target is a listed `.py`, because today's hook early-allows a `.sh`.

  ```bash
  TREE=$PWD; PY=$(command -v python3); J=$TREE/h-mad/scripts/h_mad_tdd_judge.py; H=$TREE/h-mad/hooks/h-mad-tdd-gate.sh
  R=$(cd "$(mktemp -d)" && pwd -P); S=$(mktemp -d); git -C "$R" init -q; mkdir -p "$R/docs/01-plan/features" "$R/src"; : > "$R/src/m.py"
  printf '#!/bin/sh\n' > "$S/codex"; cp "$S/codex" "$S/agy"; chmod +x "$S/codex" "$S/agy"
  printf '## Task 1: m\n**Production file**: `src/m.py`\n**Test file**: `tests/test_m.py`\n' > "$R/docs/01-plan/features/f.impl-plan.md"
  drive() { # label, then VAR=value overrides
    local label=$1; shift; local E=(HOME="$HOME" PATH="$S:$(dirname "$PY"):/usr/bin:/bin" "$@")
    local author; author=$(env -i "${E[@]}" "$PY" "$J" state --root "$R" | sed -E 's/.* record=[^,]*,[^,]*,[^,]*,([^,]*),.*/\1/')
    local line; line=$(env -i "${E[@]}" "$PY" "$J" implementer --root "$R" --feature f)
    local kind; kind=$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s/src/m.py","content":"x"}}' "$R" | env -i "${E[@]}" CLAUDE_PROJECT_DIR="$R" /bin/bash "$H" 2>/dev/null | grep -oE 'kind=[a-z-]+')
    echo "$label | state author=$author | $line | hook $kind"
  }
  printf '{"orchestrator_state":{"f":{"phase":"step5","implementer":null}}}' > "$R/docs/.bkit-memory.json"
  drive 'null  none'; drive 'null  codex' HMAD_CODEX_UNAVAILABLE=1; drive 'null  agy' HMAD_AGY_UNAVAILABLE=1
  drive 'null  both' HMAD_CODEX_UNAVAILABLE=1 HMAD_AGY_UNAVAILABLE=1
  printf '{"orchestrator_state":{"f":{"phase":"step5"}}}' > "$R/docs/.bkit-memory.json"
  drive 'unset none'; drive 'unset both' HMAD_CODEX_UNAVAILABLE=1 HMAD_AGY_UNAVAILABLE=1
  rm -rf "$R" "$S"
  ```

  Output:

  ```text
  null  none | state author=codex | TDD-IMPLEMENTER: codex chosen=codex switch=none | hook kind=codex-authorship
  null  codex | state author=agy | TDD-IMPLEMENTER: agy chosen=codex switch=codex->agy reason=env | hook kind=agy-authorship
  null  agy | state author=codex | TDD-IMPLEMENTER: codex chosen=codex switch=none | hook kind=codex-authorship
  null  both | state author=peers-out | TDD-IMPLEMENTER: claude chosen=codex switch=peers-out reason=env | hook kind=test-missing
  unset none | state author=codex | TDD-IMPLEMENTER: codex chosen=codex switch=none | hook kind=codex-authorship
  unset both | state author=peers-out | TDD-IMPLEMENTER: claude chosen=codex switch=peers-out reason=env | hook kind=test-missing
  ```

  The token that lets the Claude gate reach the judge is the state line's `peers-out`, with the implementer line `TDD-IMPLEMENTER: claude chosen=codex switch=peers-out reason=env`. Null and unset read the same in every row, so the fixture needs no `implementer` key.
- **A directory target, today.** Each hook, on the existing directory `scripts`:

  ```bash
  TREE=$PWD; PY=$(command -v python3); E=(HOME="$HOME" PATH="$(dirname "$PY"):/usr/bin:/bin")
  R=$(cd "$(mktemp -d)" && pwd -P); git -C "$R" init -q; mkdir -p "$R/scripts" "$R/.agents" "$R/docs"
  show() { sed -E 's/.*(kind=[^:"]*).*/DENY \1/' | grep . || echo 'empty stdout (ALLOW)'; }
  drive() {
    printf 'claude: '; (cd "$R"; printf '{"tool_name":"Write","tool_input":{"file_path":"%s/scripts","content":"x"}}' "$R" | env -i "${E[@]}" CLAUDE_PROJECT_DIR="$R" /bin/bash "$TREE/h-mad/hooks/h-mad-tdd-gate.sh" 2>/dev/null) | show
    printf 'codex: '; (cd "$R"; printf '{"tool_name":"apply_patch","tool_input":{"command":"*** Begin Patch\\n*** Update File: scripts\\n@@\\n-x\\n+y\\n*** End Patch\\n"},"cwd":"%s"}' "$R" | env -i "${E[@]}" "$PY" "$TREE/h-mad/hooks/h-mad-codex-tdd-gate.py" 2>/dev/null) | show
    printf 'agy: '; (cd "$R/.agents"; printf '{"toolCall":{"name":"write_to_file","args":{"TargetFile":"%s/scripts"}},"workspacePaths":["%s"]}' "$R" "$R" | env -i "${E[@]}" "$PY" "$TREE/h-mad/hooks/h-mad-agy-tdd-gate.py" 2>/dev/null) | show
  }
  echo '-- active record'; printf '{"orchestrator_state":{"f":{"phase":"step5"}}}' > "$R/docs/.bkit-memory.json"; drive
  echo '-- inactive record'; printf '{"orchestrator_state":{"f":{"phase":"step3"}}}' > "$R/docs/.bkit-memory.json"; drive
  echo '-- no docs/ on the chain'; rm -r "$R/docs"; drive
  rm -rf "$R"
  ```

  Output:

  ```text
  -- active record
  claude: DENY kind=judge-error
  codex: empty stdout (ALLOW)
  agy: DENY kind=judge-error
  -- inactive record
  claude: DENY kind=judge-error
  codex: empty stdout (ALLOW)
  agy: {"decision": "allow"}
  -- no docs/ on the chain
  claude: empty stdout (ALLOW)
  codex: empty stdout (ALLOW)
  agy: {"decision": "allow"}
  ```

  The mechanism on Claude is the first `for NAME in "${CANON_NAMES[@]}"` (the `ALL_TEST_NAMES` loop). `/bin/bash -c 'set -u; A=(); for n in "${A[@]}"; do :; done'` prints `A[@]: unbound variable` under 3.2.57. The hook's `EXIT` trap then refuses with `kind=judge-error`.

### D4 — the listing decision (FR-3, FR-4, FR-8, judge side)
New in `h-mad/scripts/h_mad_tdd_judge.py`:

```python
class PlanMatch(NamedTuple):
    plan: Path
    status: str        # "absent" | "unreadable" | "read"
    error: str         # exception class name when status == "unreadable", else ""
    matches: tuple     # ((task, base), ...): every Task whose production lists the target, first base walking up

class Listing(NamedTuple):
    value: str                   # "listed" | "not-listed" | "unreadable"
    selected: Optional[Path]     # set iff value == "listed"
    error_file: Optional[Path]   # set iff value == "unreadable"
    error: str                   # exception class name iff value == "unreadable", else ""

def _match_plans(root: Path, target: Path, records: Sequence[Record]) -> Tuple[PlanMatch, ...]
def listing(root: Path, names: Sequence[Path], records: Sequence[Record]) -> Listing:
    per_name = [(name, _match_plans(root, name, records)) for name in names]
    listed = [name for name, plans in per_name if any(m.matches for m in plans)]
    if listed:  # M:L-LISTED
        return Listing("listed", min(listed, key=lambda p: p.name), None, "")  # M:L-SELECT
    bad = next((m for _, plans in per_name for m in plans if m.status == "unreadable"), None)
    if bad:  # M:L-UNREADABLE
        return Listing("unreadable", None, bad.plan, bad.error)
    return Listing("not-listed", None, None, "")
```

- **`_match_plans` is the single home of the match.** It holds the plan-path derivation, the read, `tasks = _parse_tasks(text)  # M:W3` (that line's text moves unchanged, so `W3R`/`W3F` still match exactly once) and the ancestor walk with its realpath comparison, all lifted verbatim out of `resolve`.
- **`resolve` consumes `_match_plans`.** It rebuilds the same notes in the same order (`absent`, `impl-plan unreadable: <Exc>`, `matched`/`matched none`) and the same candidates and budget. Its `.py` output is unchanged; the existing `tdd_judge_resolution.json`, `tdd_judge_wiring.json` and `test_h_mad_tdd_judge.py` pins prove that.
- **The precedence below belongs to `listing`, not to `resolve`.** `resolve` keeps noting an unreadable plan and continuing, and no gate calls `listing` on the `.py` path. So a `.py` target beside an unreadable sibling plan reads exactly as it does today. `test_unreadable_plan_is_named_in_test_missing` and `test_unreadable_plan_with_a_passing_name_map_test_is_test_passing` stay unmodified and pin that note. A listed code-like target beside an unreadable plan reaches `judge` the same way, with that note. Residual: a plan that turns unreadable between `listing` and `judge` is noted and skipped by `resolve`, as on the `.py` path.
- **How `listing` decides.** It calls `_match_plans` once per name. The plan paths come from `records`, not from the name, so every name sees the same plans. The order is fixed:
  1. If any name has a match, the result is `listed`, whether or not another plan is unreadable (`# M:L-LISTED`). `selected` is the least listed name by `Path.name` in Python `str` order (spec FR-6 *Selection rule*; marker `# M:L-SELECT`). An unreadable plan has no `matches`, so `selected` comes from readable plans only.
  2. Otherwise, if any plan of any name is `unreadable`, the result is `unreadable`, carrying the first such plan and its exception class name (`# M:L-UNREADABLE`).
  3. Otherwise the result is `not-listed`. An `absent` plan is "not listed" (spec FR-8).
- **Why listed outranks unreadable.** This is operator ruling R-D (spec §"Assumptions", 2026-11-04). A target a readable plan lists is judged from that plan on every host, and FR-8's `kind=judge-error` applies only when no readable plan lists any of its names. Residual, accepted in R-D: an unreadable sibling can hide an earlier listed hard-link name, whose Task has different tests, so an ALLOW can come from the readable plan's Task. The AC-6.5 selection fixture shows what the same sibling does when it is readable.
- **What `listing` does not do.** It applies no doc/data rule and no exemption (spec FR-11 "The judge and the parser do not apply it"). The gates choose which names to pass.
- **FR-4.** `target_module_names` returns `frozenset()` when `Path(fold_py_suffix(target.name)).suffix != ".py"` (marker `# M:K-IMPORT-NONPY`). `fold_py_suffix` is imported from `h_mad_target_identity` beside the existing `TRUSTED_BIN_DIRS` import. A listed non-`.py` target reaches `resolve`'s `matched` branch, so the name map is never reached for it. The existing `M:R1` arm holds this, and AC-4.6 pins the backstop for the unlisted case.

**The CLI verb (FR-3, Claude transport).** `python3 h_mad_tdd_judge.py listing --root <dir> --name <path> [--name <path> …]`. `--name` uses argparse `action="append"` and `required=True`, and each value is joined to the root as `root / name`, as `--target` is today. The verb reads `read_chain(root, first name)`, then:

| Chain / listing outcome | Exact stdout line (one line) | exit |
|---|---|---|
| chain `none` | `TDD-LISTING: not-listed` | 0 |
| chain `unreadable` | `TDD-LISTING: unreadable file=<_enc(state file)> error=<chain.error>` | 0 |
| active, `listing.value == "not-listed"` | `TDD-LISTING: not-listed` | 0 |
| active, `"unreadable"` | `TDD-LISTING: unreadable file=<_enc(impl-plan)> error=<ExcName>` | 0 |
| active, `"listed"` | `TDD-LISTING: listed target=<_enc(str(selected))>` | 0 |
| any exception | nothing on stdout, `<Exc>: <msg>` on stderr | 2 |

The full value set is `listed`, `not-listed` and `unreadable`, three values, one each for listed, not listed and unreadable (spec FR-3). Chain `none` maps to `not-listed` because both mean ALLOW and the spec requires exactly three values. Every `error=` value is an identifier: `_state_at` returns `type(exc).__name__`, `not-a-regular-file` or `not-an-object`, and the plan read returns `type(exc).__name__`. This is the same form `STATE_UNREADABLE_RE` accepts. `TDD-STATE:`, `TDD-JUDGE:` and `WIREPIN:` are untouched.

### D13 — the doc/data definition (FR-11)
New in `h-mad/scripts/h_mad_target_identity.py`, the module both Python gates already import (plan M10):

```python
DOC_DATA_SUFFIXES = (".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".rst", ".cfg", ".ini")
_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")

def has_doc_data_suffix(name: str) -> bool        # end-of-basename, ASCII case-insensitive  (# M:G-DOCDATA-CASE)
def is_doc_data(names: Sequence[str]) -> bool      # all(has_doc_data_suffix(n) for n in names)  (# M:G-DOCDATA-ALL)
def emit_doc_data(identity: Identity) -> None      # prints exactly "docdata yes" or "docdata no"
def _is_exempt_location(relative: str) -> bool     # parent parts: first == "docs", or "tests"/"fixtures" in them
```

- **Suffix matching.** `has_doc_data_suffix` compares `name[-len(s):].translate(_ASCII_LOWER) == s` for each `s`. That is the spec's end-of-basename, ASCII-only rule: a dotfile named exactly `.md` and `a.tar.md` qualify; `x.md.sh`, `x.mdx` and `x.jsonl` do not. `str.lower()` is not used, because it folds non-ASCII letters too.
- **The empty-names case.** `is_doc_data(())` is vacuously `True`. A directory is the only resolvable identity with no names (premise above). No host's verdict for a directory changes, and this feature adds no allow path for one (§"A directory target, today"):
  - **Claude.** Where the chain cannot hold state, `_chain_may_hold_state … || _allow` allows first, as today. Where it may hold state, an inactive record included, the unguarded `ALL_TEST_NAMES` loop stops the script under `set -u`, and the verdict is `kind=judge-error`. `# M:H-DOCDATA` sits after that loop, so the `docdata yes` line a directory prints is parsed and then never read. Residual: a `/bin/bash` newer than 3.2 does not stop on that expansion. Running today's hook with `/opt/homebrew/bin/bash` 5.3.20 (the directory block's Claude line with that path in place of `/bin/bash`) on the active-record case gives ALLOW, because the empty loop leaves `ALL_TEST_NAMES` at `yes`. This feature edits neither line, so that verdict does not change either. `/bin/bash` 3.2 remains this gate's stated constraint.
  - **codex.** `# M:CX-DOCDATA` now skips the target first, where today's skip is `if not production`. The verdict stays ALLOW.
  - **agy.** T2a decides before `# M:AG-DOCDATA`: deny on an active or unknown status, `continue` on an inactive one.
- **`_is_exempt_location`.** This is the path half of `_is_production_python`, read over parent components so that a file literally named `tests` stays non-exempt, as Claude's `_dir_match` (`*/tests/*`) already treats it. `_is_production_python` is not edited; it keeps the `# M:G-DOCS` marker and its `target_identity.json` anchors. A parity test pins `_is_production_python(d + "/m.py") == (not _is_exempt_location(d + "/m.py"))` over a directory corpus that includes `docs`, `src/docs`, `tests`, `a/tests/b`, `fixtures`, `docs.py` and the root.

**D13 decision: the Claude gate uses the definition, not a copy.** The `# M:H11` line becomes:
`…from h_mad_target_identity import canonicalise,emit_canon,emit_doc_data;i=canonicalise(sys.argv[2],sys.argv[3]);emit_canon(i);emit_doc_data(i)' … # M:H11`.
The gate then does three things:
1. Before `_read_canon`, it splits the last line off: `DOC_DATA_LINE=${CANON_RECORD##*$'\n'}; CANON_RECORD=${CANON_RECORD%$'\n'*}`.
2. After `_read_canon`, it accepts exactly `docdata yes` or `docdata no` and otherwise runs `_refuse judge-error "invalid docdata line"`. CANON errors therefore keep their own reasons.
3. It replaces the whole `ALL_SUFFIX_NAMES` loop and its allow with `[ "$DOC_DATA" = yes ] && _allow  # M:H-DOCDATA`, at the same position: after the path exemptions, before any state read.

The split is the first construct probed in §"The bash 3.2 constructs".

History: why the pinned copy an earlier plan revision allowed was not taken. Spec v1.6 and plan v1.4 adopted this decision and retired the copy option, so it is not open. The reasons stay here as its rationale:
- **Process budget.** It starts no process. The canonicalise process runs on every write today, before the doc/data check, so the doc/data allow still costs zero new processes (spec NFR). Calling the predicate in a separate `python3` would cost one per write. That was the pressure toward a copy; it does not apply here.
- **AC-11.6.** Its first sentence ("removes one suffix from the shared definition turns that suffix's AC-11.3 case from ALLOW to DENY on all three hosts") cannot hold on Claude under a copy, because a mutated Python definition leaves a bash copy unchanged. With the gate using the definition, it holds on all three hosts.
- **R11 (copy drift).** There is no copy, so nothing can drift.
- **R12 (`nocasematch` leakage).** No bash case-insensitive construct is used. `shopt` is never called, so no later `case` in the gate (the `_fold_py` arms, the `# M:H6` test-name arm, the `!= *.py` loop) can change. This is the spec's *No bash matcher* term: there is no bash construct, and the case fold is `str.translate` in Python.
- **R13 (the three markers of `test_py_suffixes_match_bash_fold`).**
  - `# M:H6`: kept, unchanged.
  - `!= *.py`: kept. The `ALL_NON_PY` loop stays byte-identical, and only the allow that follows it is replaced.
  - `*.md|*.yaml`: removed with the arm it marked. *Regression provenance:* the test asserts that each per-name classification site reads a `_fold_py`-folded name. The doc/data classification is no longer a bash site, and folding is irrelevant to it (`fold_py_suffix` changes only `.py` spellings, none of which is a doc/data suffix). So the marker pinned a site that no longer exists; it did not pin a defect. Task 6 replaces it in the test's marker tuple with an assertion that the `# M:H11` line contains `emit_doc_data(i)` and that `ALL_SUFFIX_NAMES` no longer occurs in the hook. The suffix pin is not part of this edit: `test_doc_data_suffixes_are_the_spec_nine` is Task 2's RED pin (§Implementation Order).

### Claude gate (`h-mad/hooks/h-mad-tdd-gate.sh`, D6; FR-5, FR-8, FR-11, NFR)
Everything up to and including the path exemptions is unchanged, except the `# M:H11` tail and the docdata split above. After the exemptions:

```bash
[ "$DOC_DATA" = yes ] && _allow  # M:H-DOCDATA
ALL_NON_PY=yes
PRODUCTION_TARGET=
for NAME in "${CANON_NAMES[@]}"; do  ...unchanged loop with `!= *.py` and its continue...
done
if [ "$ALL_NON_PY" = yes ]; then
  [ "$IN_ROOT" = yes ] || _allow  # M:H-LIST-INROOT  (out-of-root is exempt; spec Terms)
  _find_judge
  _read_listing  # M:H-LIST   <- the AC-3.1 Claude connection site
  TARGET_PATH=$LISTED_TARGET
else
  TARGET_PATH=$PRODUCTION_TARGET
fi
_find_judge
_read_state --target "$TARGET_PATH"  # M:H3   (unchanged from here to the end, except one added line: # M:H-LIST-CONTEXT)
```

The second `_find_judge` call starts nothing on the code-like branch: the function returns at once when `JUDGE` is already set (`[ -n "$JUDGE" ] && return 0`).

`_read_listing` follows the `_read_state` shape:
- **The launch.** `LOUT=$(python3 "$JUDGE" listing --root "$ROOT_ABS" ${LARGS[@]+"${LARGS[@]}"} 2>/dev/null; printf 'rc=%s' "$?")  # M:W7`. `LARGS` holds `--name ${CANON_TARGET%/*}/$NAME` for every canonical name, the same expression `PRODUCTION_TARGET` uses. The `${a[@]+…}` guard is the bash-3.2 form that expands nothing under `set -u` for an empty array (§"The bash 3.2 constructs"). The array cannot be empty here: an empty name set never gets past the `ALL_TEST_NAMES` loop and the allow that follows it.
- **Line count.** Zero or several lines → `_refuse judge-error "listing verb printed zero or several lines"`.
- **Exit status.** `LRC != 0` → `_refuse judge-error "listing verb exited rc=$LRC"` (`# M:H-LIST-RC`).
- **Not listed.** `TDD-LISTING: not-listed` → `_allow`.
- **Unreadable.** A match of `^TDD-LISTING: unreadable file=([^ ]+) error=([A-Za-z_-][A-Za-z0-9_-]*)$` → `_refuse judge-error "listing is undecidable (<decoded file>: <error>)"  # M:H-LIST-UNREADABLE`.
- **Listed.** A match of `^TDD-LISTING: listed target=([^ ]+)$` → `_pct_capture LISTED_TARGET "${BASH_REMATCH[1]}"  # M:H-LIST-DECODE`, which must equal one of the `--name` values passed, else `_refuse judge-error "listing verb named a target it was not given"` (`# M:H-LIST-NAME`). `_pct_capture` is the hook's existing decoder for canonical names. A bare `$(_pct_decode …)` strips trailing newlines, and a listed symlink can resolve to a name ending in one (§Test Strategy, "Newline-ending name").
- **Anything else** → `_refuse judge-error "listing verb printed no well-formed listing line"`.

The `([^ ]+)` capture matches what `STATE_UNREADABLE_RE` does for `file=`, because `_enc` leaves `~` unescaped.

FR-5 order, as shipped:
- **Steps 1 and 2 run in one process.** The `listing` verb performs the state read (`read_chain`; `none` → `not-listed` → ALLOW, `unreadable` → judge-error) and then the listing decision, in that order. The spec NFR permits this merge ("merging the state read and the listing decision into one process").
- **Step 3.** For a listed target, `_read_state --target` and the implementer, peer and fallback refusals then run unchanged.
- **Step 4.** The judge receives the selected listed name.
- **Listed-target deny context (`# M:H-LIST-CONTEXT`).** `git diff -U0 e097dfcb 38dd84a6 -- h-mad/hooks/h-mad-tdd-gate.sh` (the replay base to the verified tree) shows one change below `# M:H3`: this line, added between `# M:H4` and the hook's existing deny arm.

  ```bash
  if [[ $JOUT =~ $JUDGE_DENY_RE ]] && [ "$ALL_NON_PY" = yes ]; then _refuse "${BASH_REMATCH[1]}" "target=$TARGET_PATH: ${BASH_REMATCH[2]}"; fi  # M:H-LIST-CONTEXT
  ```

  - **Why it exists.** The selected name can differ from the name written: in AC-6.5's S2 state a write to `scripts/tool.sh` is judged as `scripts/hard.sh`, and the judge's reason names only the test and the plan.
  - **What it cannot change.** It keeps the judge's kind and prefixes only the reason. Without the line, the next arm refuses on the same match with the same kind, so the verdict and kind are the same either way. It is gated on `ALL_NON_PY`, so `.py` output is untouched.
  - **Host parity.** All three hosts name the selected target in a listed-target deny, in their own form: Claude prints `target=<absolute canonical path>: `, and codex and agy print `before <root-relative path>: ` from `listed.selected`. Reading at `38dd84a6`, on the S2 state of `non_py_gate_support.selection_fixture`: all three name `scripts/hard.sh`. One asymmetry remains on `.py`: the codex and agy deny wording names the target on that path too, and Claude's does not.
  - **Pin.** Row `H-LIST-CONTEXT` in `claude_gate_listing.json`, killed by `test_claude_selection_s2_denies`, which asserts `scripts/hard.sh` in the reason. Residual, stated exactly: the pin reads one kind, `test-missing`; no test asserts the prefix on another `JUDGE_DENY_RE` kind.
- **Cost of a listed target.** Its chain is read twice (by `listing`, then by `state`). The `judge` verb reads it a third time, as it does today for `.py`.

**NFR — shipped Claude-gate process count.** For an unlisted code-like write where state exists, the gate starts **2** extra short Python processes: `_find_judge` (`# M:W6`) and `listing` (`# M:W7`). Today that write starts 0, because `ALL_SUFFIX_NAMES` or `ALL_NON_PY` allows it. The spec ceiling is 3. Other cases:
- A doc/data write: 0 extra, in every state.
- An unlisted code-like write with no `docs/.bkit-memory.json` on the chain: 0 extra (`_chain_may_hold_state`).
- A listed code-like write: also `state` and `judge`, and the pytest run (the spec makes listed targets pay it).

`_find_judge` is kept unchanged. Deriving the judge path in bash (`BASH_SOURCE` plus `cd -P`) would save one more process, but `# M:W6` is shared with the `.py` path and pinned by `W6R`/`W6F`. Also, `cd -P` resolves directory symlinks but not a symlinked hook *file*, which would need a `readlink` loop in bash 3.2. That is a new failure surface on every `.py` write, bought for one process the budget does not require.

### codex gate (`h-mad/hooks/h-mad-codex-tdd-gate.py`, D7; FR-6, FR-8, FR-11)
Additions to the existing module-level `from h_mad_target_identity import (…)` block: `is_doc_data`, `_is_exempt_location`, `fold_py_suffix`. In the per-target loop (`# M:G5`), after the `# M:SA-GUARD` check and before `production = []`:

```python
        if is_doc_data(resolved.names):  # M:CX-DOCDATA
            continue
```

The existing `if not production:\n            continue` becomes:

```python
        if not production:
            reason = _judge_listed(root, resolved)
            if reason:
                return _deny(reason)
            continue
```

`_judge_listed(root, resolved) -> str` is a module-level function. It returns `""` for skip or allow, and a deny reason otherwise:
1. **Not code-like.** If any name folds to `.py`, return `""`. Such a target has only test-shaped `.py` names (no production name, or `production` would be non-empty), so it is not code-like (spec Terms *Non-`.py`*) and is skipped as today (FR-6 step 2).
2. Build `names = [Path(resolved.target).parent / n for n in resolved.names]`.
3. **Exempt.** If `_is_exempt_location(names[0].relative_to(root).as_posix())`, return `""` (`# M:CX-LIST-EXEMPT`). All names share one directory, so one check covers all of them.
4. **Chain.** `judge = _load_judge()`, then `chain = judge.read_chain(root, names[0])`. `unreadable` → `"H-MAD state governing this write is unreadable (<file>: <error>); refusing fail-closed. kind=judge-error"`. Not `active` → `""` (FR-6 step 3).
5. **Listing.** `listed = judge.listing(root, names, chain.records)  # M:CX-LIST`, the codex connection site for AC-3.1. `unreadable` → `"H-MAD Phase 5 listing is undecidable (<file>: <error>); refusing fail-closed. kind=judge-error"`. `not-listed` → `""` (FR-6 step 4).
6. **Judge.** `verdict = judge.judge(root, listed.selected, chain.records)`. Non-ALLOW binds `relative = listed.selected.relative_to(root).as_posix()` and returns `f"H-MAD Phase 5 requires a failing test before {relative}: kind={verdict.kind}; {verdict.reason}"`, the existing deny wording (FR-6 step 5). `listed.selected` is one of `names`, whose parent `_relative_target` has already placed under `root`, so `relative_to` cannot raise here.

The `.py` branch (`min(production)`, `# M:W5A`, `# M:W1`) is not edited. Exceptions still reach `# M:G2` as `kind=judge-error`. `test_codex_gate_keeps_no_private_resolver` stays green, because no banned token is introduced.

### agy gate (`h-mad/hooks/h-mad-agy-tdd-gate.py`, D8; FR-7, FR-8, FR-11)
One addition to the existing in-`main` import from `h_mad_target_identity`: `_is_exempt_location`. `is_doc_data` is not imported by name. Its call goes through `identity`, which `main` binds with `import h_mad_target_identity as identity` just above that import and which T1–T2 already use (`identity.canonicalise`). After the `# T6–T7` comment and before `                production = []`:
`if identity.is_doc_data(resolved.names): continue  # M:AG-DOCDATA`.

This does not duplicate the `production = []` anchor text, so `fr4-t6-t7-skipped-when-inactive` still matches exactly once. The existing `if not production:` / `continue` becomes an inline block running the same six steps as codex's `_judge_listed`, through the `judge` name `main` already binds (`identity.fold_py_suffix`, `judge.read_chain`, `listed = judge.listing(root, names, chain.records)  # M:AG-LIST`, `judge.judge`). Step 6 binds `relative` from `listed.selected` as codex does, which replaces the value the `for name` loop left in `main`'s `relative`. Two differences from codex:
- Denies use agy's form: `{"decision": "deny", "reason": "… kind=<kind>"}`, with `detail.replace("kind=", "kind:")` as in the existing T6–T7 deny.
- The judge-error reasons are `"State governing the write is unreadable (…). kind=judge-error"` (existing wording) and `"Listing is undecidable (…). kind=judge-error"`.

T1–T5 are unchanged and run first.

### AC-3.1 mutants — the connection site per host
Each mutant anchors one line, which must occur exactly once (the harness's landing check). Each mutant runs with its own host's test file only.

| Host | Connection site (anchor) | Remove → killed by | Force → killed by |
|---|---|---|---|
| Claude | `  _read_listing  # M:H-LIST` | replace with `  _allow  # M:H-LIST`; `test_claude_listed_absent_test_denies` (AC-5.1) | replace with `  LISTED_TARGET=$CANON_TARGET  # M:H-LIST`; `test_claude_unlisted_code_like_allows` (AC-5.4) asserts ALLOW, and the mutant gives a DENY of *any* kind (P5-1: under the Claude-author arrangement it reaches the judge as `no-test-resolved`; under default authorship it is a codex-authorship refusal) |
| codex | `listed = judge.listing(root, names, chain.records)  # M:CX-LIST` | `listed = judge.Listing("not-listed", None, None, "")  # M:CX-LIST`; `test_codex_listed_absent_test_denies` (AC-6.1) | `listed = judge.Listing("listed", min(names, key=lambda p: p.name), None, "")  # M:CX-LIST`; `test_codex_unlisted_code_like_allows` (AC-6.3) |
| agy | `listed = judge.listing(root, names, chain.records)  # M:AG-LIST` | as codex, `# M:AG-LIST`; `test_agy_listed_absent_test_denies` (AC-7.1) | as codex; `test_agy_unlisted_code_like_allows` (AC-7.3) |

The codex and agy anchors differ only by their markers, so each occurs exactly once in its own file. The callee mutant replaces `listing`'s first body line with `return Listing("not-listed", None, None, "")`. It is entered three times, once per host, with the AC-5.1, AC-6.1 and AC-7.1 tests respectively. Claude's remove, force and callee entries score tests that run under the Claude-author arrangement (§Test Strategy), so no authorship refusal stands between the mutant and the judge.

### FR-1 and FR-2 — parser and wire-pin (D1–D3)
In `_parse_tasks` (`h-mad/scripts/h_mad_wire_pin_gate.py`), the `current["ungated"].extend(…)` branch under `if key == "production":` becomes `current["production"].extend(token for token in _NON_PY_PATH_RE.findall(…) if not token.endswith(".py"))  # M:P-NONPY`. Order is preserved: the `.py` tokens of a line first, as today, then its non-`.py` tokens in line order. A line without non-`.py` tokens is therefore unchanged in items and order (AC-1.2).

**Consumer-level coverage of the parser.** `_parse_tasks` is private, so the parser unit tests are supplementary, and these five tests in `h-mad/tests/test_h_mad_parse_tasks_non_py.py` drive the real parser through public CLIs. `check()` and wire-pin's `main` print nothing from `production` or `tests`, so a wire-pin run alone cannot observe AC-1.1 to AC-1.4. The judge is the parser's reader there, and `h_mad_tdd_judge.py judge` exists before Task 1. Each CLI runs under `sys.executable`, the suite's interpreter, which holds pytest.
- `test_judge_cli_finds_each_token_of_a_mixed_production_line` (AC-1.1): on the AC-1.1 line with `**Test file**: `tests/test_t.py`` absent, each of the three targets reads `kind=test-missing`. Before the edit the `.sh` and the extensionless target read `kind=no-test-resolved`.
- `test_judge_cli_keeps_a_python_only_line` (AC-1.2): a listed `src/m.py` with a failing test reads `ALLOW kind=red-measured source=impl-plan test=tests/test_m.py`. Green before the edit (control).
- `test_judge_cli_ignores_a_none_production_value` (AC-1.3): on the AC-1.3 line, `docs/x/run.sh` reads `kind=no-test-resolved`. Green before the edit (control).
- `test_judge_cli_ignores_a_non_py_test_token` (AC-1.4): with a listed `scripts/x.sh` and an existing `h-mad/tests/mutation-specs/x.json` on the **Test file** line, the target reads `kind=test-missing` with no candidate. Before the edit it reads `kind=no-test-resolved`. With `tests` widened it reads `kind=no-tests-ran`.
- `test_wire_pin_cli_output_ignores_a_non_py_token` (AC-1.5): `h_mad_wire_pin_gate.py <plan> --feature f --registry <file>` on a `wiring` Task, with and without a `.sh` token on its **Production file** line, prints the same stdout and writes the same registry record apart from `registered_ts`. Before the edit the stdout differs by the `ungated:` line.

Readings at `09a309ca`, on the HEAD scripts and on a scratch tree carrying the `# M:P-NONPY` edit. The prototype was deleted after the run.

The following are deleted: the `"ungated": []` key, `_ungated_entries`, the `ungated` local in `check()`, both `"ungated": ungated` result entries, and the `main` print loop. The comments at `_NON_PY_PATH_RE` and at `path_labels` ("`production`/`tests` keep only `.py` tokens") are reworded to the new truth (only `tests` is `.py`-only).

The six `…ungated…` test functions in `test_h_mad_wire_pin_gate.py` are retired. (Count command: `grep -cE '^def test_[a-z_]*ungated' h-mad/tests/test_h_mad_wire_pin_gate.py` gives 6; their names are listed under `rtk proxy grep -n 'ungated'` on that file.) Retirement is the regression-provenance case "stale contract": each asserted that the `ungated` surface FR-2 retires exists. Replacements:
- `test_a_shell_production_file_is_collected_in_production` (U1's guarantee)
- `test_an_extensionless_production_path_is_collected_in_production` (U2's guarantee)
- `test_cli_prints_no_ungated_line` (AC-2.1)
- `test_check_and_tasks_carry_no_ungated_key` (AC-2.2)
- `test_an_unshaped_plan_with_a_non_python_token_stays_unshaped` (AC-2.3)

`wire_pin_ungated.json` keeps its filename, so AC-2.4's "mutation run over that spec" stays runnable:
- **U1** re-anchors on the `# M:P-NONPY` extend, which the mutant replaces with `pass`, and re-points at the `.sh` test.
- **U2** keeps its `_NON_PY_PATH_RE` anchor and replaces it with a dot-required pattern. It re-points at the extensionless test.
- **U3, U4 and U5** are retired. Their guarantees ("python not ungated", "UNSHAPED keeps the key", "CLI prints the line") assert the retired surface itself. `_why` records this.

### FR-10 — prose (D9)
**Widened phrasing set (AC-10.1 plus three branches):**
`production-Python|a .\.py. suffix in any case|never gated|only production|production-.\.py.|markdown / yaml|Both gates|neither gate`

Each added branch's pre-change hit, run alone with `git grep -n -E '<branch>' -- h-mad/SKILL.md h-mad/references h-mad/agents h-mad/invariants.base.md` at `4bf4ee4c`:
- `markdown / yaml` → 1 matching line: `codex-implementer-prompt.md`, the doc/data Hook bullet (inside surface 1). It names six of the nine suffixes.
- `Both gates` → 2 matching lines: the test-file Hook bullet of `codex-implementer-prompt.md` (surface 1) and the `Both gates apply this same rule.` sentence of `phase5-substeps.md` (surface 3). Three gates apply both rules today (spec FR-10 provenance), so both lines state a stale count.
- `neither gate` → 1 matching line, the same test-file Hook bullet ("a target neither gate can resolve"). It is the same two-gate count.

The whole eight-branch command prints 7 matching lines in 3 files, holding 9 occurrences (`git grep -o -h -E '<regex>' -- <same pathspecs> | wc -l`). **Surfaces added: zero.** Every added hit sits inside surface 1 (the `Hook: ` line plus its `- ` bullets) or surface 3. Three other candidate phrasings were also run and are **not** added:
- `allowed unconditionally`: 3 matching lines. It stays true for the test-file and docs-first bullets.
- `is not gated`: `phase5-substeps.md`, where it states the unchanged docs-first exemption.
- `production-code write` / `production write`: `agy-runtime.md` §"The TDD gate" and `grok-runtime.md` §"The TDD gate". A listed `.sh` is production code, so these stay true.

Residual, stated exactly: a rule statement outside the four locators that uses none of the eight phrasings, and a phrasing split across a hard wrap.

**New text (Task 7; each sentence avoids all eight branches).**
- **Surface 3** (`phase5-substeps.md`). The paragraph's first sentence is replaced by the AC-10.3 anchor, which must occur exactly once in `doc_text(SKILL)`:
  `The gates judge production `.py`, and a code-like file such as a `.sh` script or an extensionless launcher when a Task's **Production file** line lists it; test files, docs, doc/data files (`.md` `.yaml` `.yml` `.json` `.toml` `.txt` `.rst` `.cfg` `.ini`, listed or not) and unlisted code-like files are allowed.`
  The docs-first sentences follow unchanged, so the four docs-first tokens stay in the paragraph after the anchor. `Both gates apply this same rule.` becomes `All three gates apply this same rule.`
- **Surface 4.** "refuses Claude's production-`.py` write" becomes "refuses Claude's write to production `.py` or to a listed code-like file".
- **Surface 2.** "production-Python writes" becomes "writes to production `.py` and to listed code-like files (such as a `.sh` script a Task's **Production file** line names)".
- **Surface 1.**
  - The test-file bullet gets "All three gates judge a path by its resolved identity …; a target no gate can resolve …".
  - The doc/data bullet becomes "The path is a doc/data file — every resolved name ends in `.md`, `.yaml`, `.yml`, `.json`, `.toml`, `.txt`, `.rst`, `.cfg` or `.ini`, in any case — allowed, even when a Task lists it."
  - The production bullet becomes "For production `.py` (any case of the suffix, `.PY` included), …".
  - A new bullet: "For a code-like file — a `.sh` script, an extensionless launcher, any suffix outside the nine — that a Task's **Production file** line lists, the test comes from that Task only (there is no name map); allow the write only if it exists and pytest's summary shows `N failed`. An unlisted code-like file is allowed."
  - All existing tokens of `test_hook_bullets_state_the_shipped_rule` remain, and no `<`/`>` is introduced.
- **The `listing` verb's documentation.** `h-mad/references/helper-scripts.md`'s `h_mad_tdd_judge.py` entry gains the `listing` verb and its `TDD-LISTING:` values. `test_helper_scripts_registers_the_judge` gains the tokens `listing` and `TDD-LISTING:`. This keeps the new value set named once in prose and pinned (plan Architecture "Enumerated CLI contract").

### FR-9 — the driver (D12, D14)
- **Driver.** `docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py`. It is a committed probe, stdlib only, outside pytest's `testpaths` (`h-mad/tests handoff/tests handoff/scripts`, per `pytest.ini`), and exempt from all three gates as a root-`docs/` file. Usage: `python3.11 -I fr9_drive.py --scenario fixture|replay --side after|before --host claude|codex|agy --out <evidence dir>`. The driver runs one host per invocation, so no host's run can cover another's. The tree under test is the current directory's `git rev-parse --show-toplevel`, not the driver's own location.
- **Hermetic environment.** It reproduces `hermetic()` from the read-only method reference `/Users/kimhawk/orca/skills/.claude/skills/verify-hmad-gates/bin/hmad-verify.sh`: `env -i HOME=… PATH=… LANG=${LANG:-en_US.UTF-8} TMPDIR=…`, passed as `subprocess.run(env=…)` and recorded in the evidence. There are three additions, for the Claude host only and on both sides, all recorded. `CLAUDE_PROJECT_DIR=<scratch root>` is there because the hook reads it and a real session sets it. `HMAD_CODEX_UNAVAILABLE=1` and `HMAD_AGY_UNAVAILABLE=1` are the spec's Claude-author arrangement (§"Fixture"), which `env -i` would otherwise drop.
- **Authorship check.** Before each Claude-host verdict the driver runs that side's `h_mad_tdd_judge.py implementer --root <root> --feature <key>`, without `--record`, in the hook's environment. The key is `f` for the fixture and `exec-missing-report-recovery` for the replay. It stores the line as `implementer.txt` and requires exactly `TDD-IMPLEMENTER: claude chosen=codex switch=peers-out reason=env`. Any other line prints `FR9-DRIVE: UNREADABLE authorship-line` with exit 2, because spec §"Fixture" makes such a run invalid rather than failed.
- **Real stdin entry points.**
  - Claude: `/bin/bash <hook>` with stdin `{"tool_name":"Write","tool_input":{"file_path":"<abs>","content":"x"}}`, cwd = root.
  - codex: `python3 <hook>` with `{"tool_name":"apply_patch","tool_input":{"command":"*** Begin Patch\n*** Update File: <rel>\n@@\n-x\n+y\n*** End Patch\n"},"cwd":"<root>"}`, cwd = root.
  - agy: `python3 <hook>` with `{"toolCall":{"name":"write_to_file","args":{"TargetFile":"<abs>"}},"workspacePaths":["<root>"]}`, cwd = `<root>/.agents`. That is where agy runs it: the gate takes `git -C Path.cwd().parent`. The driver creates `<root>/.agents` in every scratch root before the agy call, on both scenarios, because `subprocess.run` raises `FileNotFoundError` on a missing cwd before the hook starts.
- **Hook identity (AC-9.2).** For the after side, the driver refuses (`FR9-DRIVE: UNREADABLE dirty-hooks`) unless `git status --porcelain -- h-mad` prints nothing. For each executed hook it then requires the realpath to lie under `git rev-parse --show-toplevel` (`FR9-DRIVE: UNREADABLE hook-outside-tree`), and after that requires `git hash-object` of the file and `git rev-parse HEAD:<path>` to agree (`FR9-DRIVE: UNREADABLE hook-blob-mismatch`). The realpath check comes first because a committed symlink's blob is its link text while `git hash-object` reads the file it points to, so the blob check would otherwise report every out-of-tree symlink as `hook-blob-mismatch`. It records the realpath, sha256 and both blob ids. The realpath check excludes `~/.claude/skills/h-mad` and the helper's installed paths, which resolve to `/Users/kimhawk/orca/skills/h-mad` (plan M7).
- **Before tree (D14, R15).** The base is `git merge-base HEAD origin/main`. The driver re-derives it at run time and records it; its value is not pinned here. On `--scenario replay`, a missing `origin/main` refuses with `FR9-DRIVE: UNREADABLE missing-base`. The driver materialises every `h-mad/` file at that commit with `git archive <base> h-mad | tar -x -C <mktemp dir>`. This only reads the repository, so it touches neither this worktree nor the shared ref store. It records the before-side hook realpath and sha256 per host. Taking the whole `h-mad/` tree covers the judge's lazy imports (`h_mad_state_write` and its `h_mad_bkit_guard`, `h_mad_state_ownership` and `h_mad_state_validate`; P5-2) and `h_mad_wire_registry`'s CLI-only import of `h_mad_assemble_tdd` (PF-1) by construction.
- **Evidence is taken before the Phase 7 push.** Once this branch is on `origin/main`, `git merge-base HEAD origin/main` returns HEAD, so the before tree equals the after tree and AC-9.4's incident row reads DENY on both sides. On `--scenario replay`, either side, the driver refuses with `FR9-DRIVE: UNREADABLE base-is-head` and exit 2 when the base equals HEAD. A refusal fits better than a FAIL row, because that reading would say nothing about the spec's premise. This refusal does not apply to the fixture scenario, which has no before tree. Residual: a base other than HEAD whose `h-mad/` equals the commit under test passes this check, and its incident row then reads as a FAIL row (§"Verdict token").
- **Replay repo (AC-9.4, AC-9.5).** The driver builds it by `git init` in a mktemp dir. `<commit>` below is the before tree's base, `git merge-base HEAD origin/main`, on both sides. Reading at `3ff9ea4a`: that base is `83009078`, and `git rev-parse <base>:docs/01-plan/features/exec-missing-report-recovery.impl-plan.md` prints the same `fef082989979cd8a7a1c0f896db4673a14e078e2` the spec read at `e4979ecd`. The design does not use `e4979ecd`, which `git branch -a --contains e4979ecd` shows only on `backup/gate-non-py-pre-rebase-767be799`. Residual: if `origin/main` moves past a commit that edits this plan, the blob moves with the base. AC-9.5's provenance records which blob the run used, and the AC-9.4 rows then read that text.
  - It writes `docs/01-plan/features/exec-missing-report-recovery.impl-plan.md` from `git cat-file blob <commit>:<that path>` bytes. A non-zero exit there refuses with `FR9-DRIVE: UNREADABLE plan-absent-at-base` (`# M:D-PLAN-ABSENT`). It records the commit, `git rev-parse <commit>:<path>` (today `fef082989979cd8a7a1c0f896db4673a14e078e2`, plan M12) and the copy's sha256, and requires `git hash-object <copy>` to equal the blob id (`FR9-DRIVE: UNREADABLE plan-blob-mismatch`).
  - It writes `docs/.bkit-memory.json` with `orchestrator_state.exec-missing-report-recovery = {"phase": "step5"}`, the same record for all three hosts. It holds no `implementer` key, because null and unset both select codex (§"Who authors on the Claude host"); Claude's authorship comes from the environment.
  - It creates `h-mad/scripts/hmad-dispatch.sh`, `h-mad/SKILL.md` and `h-mad/scripts/h_mad_derive_test_path.sh`. Their content does not affect the verdict.
  - It runs `h-mad/tests/test_hmad_dispatch_exec.py` absent, then as `def test_red(): assert False`.
  - It drives the four AC-9.4 rows per host and per side.
- **Fixture scenario (AC-9.1).** It uses spec §"Fixture" verbatim, under the Claude-author arrangement on the Claude host: three rows per host, after side only. `--scenario fixture --side before` refuses with `FR9-DRIVE: UNREADABLE no-before-side`.
- **Refusals.** The driver prints nine `FR9-DRIVE: UNREADABLE` reasons, each with exit 2. `h-mad/tests/test_h_mad_fr9_drive_refusals.py` holds one node per reason, because `docs/` is outside `testpaths`. Each node runs the real driver by path, with the current directory in a throwaway `git init` repo that holds committed copies of `h-mad/hooks` and `h-mad/scripts`, and asserts the token line and exit 2. `fr9_drive_refusals.json` holds one mutation row per reason, each killed by that reason's node. That test names the probes directory, so `h_mad_archive_feature.py` keeps the directory in place. The fixtures:
  - `no-before-side`: `--scenario fixture --side before`.
  - `dirty-hooks`: an uncommitted edit to the executed hook.
  - `hook-outside-tree`: the executed hook committed as a symlink to a file outside the repo.
  - `hook-blob-mismatch`: an edit to the hook hidden by `git update-index --assume-unchanged`, so `git status --porcelain` prints nothing and `git hash-object` differs from `HEAD:<path>`.
  - `authorship-line`: a committed `h_mad_tdd_judge.py` stub whose `implementer` verb prints `TDD-IMPLEMENTER: codex chosen=codex switch=none`.
  - `missing-base`: `--scenario replay` with no `refs/remotes/origin/main`.
  - `base-is-head`: `--scenario replay` with `refs/remotes/origin/main` at HEAD.
  - `plan-absent-at-base`: `--scenario replay --side after`, a base without the plan path, a later HEAD adding it, `refs/remotes/origin/main` at the base, so `git cat-file blob <base>:<path>` exits 128.
  - `plan-blob-mismatch`: `--scenario replay --side after`, with the base commit holding a CRLF plan, a later HEAD, `refs/remotes/origin/main` at the base, and `core.autocrlf=true` in the fixture repo's local config, so `git hash-object` normalises the copy and differs from the blob id. The setting travels in the repo's config because the driver passes no `GIT_*` variable to `git`.

  Residual, stated exactly: an uncaught exception, such as a missing `git`, exits 1 with no token and reads as no verdict.
- **Evidence folder.** `docs/03-analysis/probes/gate-non-py-production-files/fr9/<UTC-stamp>-<HEAD sha12>/`. It holds:
  - one `NNN-<scenario>-<side>-<host>-<case>/` directory per call, with `stdin.json`, `stdout`, `stderr`, `rc`, `argv.json`, `env.json`, `hook.json` (path, sha256, blob ids) and, on the Claude host, `implementer.txt`;
  - `provenance.json` (commit under test, base, plan blob, copy sha256, `python3` realpath and version);
  - `readings.tsv`, one row per call with the host-form verdict.
- **Verdict token.** The driver compares `readings.tsv` against the AC-9.1 and AC-9.4 tables and prints `FR9-DRIVE: PASS rows=N mismatched=0` or `FR9-DRIVE: FAIL rows=N mismatched=M`, with exit 0 on either verdict. A before reading other than ALLOW is a FAIL row, never a pass (spec AC-9.4).
- **Interpreter.** Each scratch root gets `<root>/.venv`, built with `sys.executable -I -m venv --without-pip --system-site-packages`, on both sides and every host, and `provenance.json` records that interpreter. The judge's `select_interpreter` finds it by walking up from the test, so a listed-failing row does not depend on the `python3` the hermetic `PATH` offers. Reading at `09a309ca`, on the HEAD hooks, a listed `.py` with a failing test and `PATH=/opt/homebrew/bin:/opt/anaconda3/bin:/usr/bin:/bin`: `kind=pytest-missing` on all three hosts without the venv, and ALLOW on all three with it. The driver must run under an interpreter whose site-packages hold pytest, hence `python3.11` in the usage line. Otherwise the listed-failing rows read `pytest-missing` and print `FR9-DRIVE: FAIL`, never a pass.

### Phase 7 integration target (PF-3)
The feature integrates into the **local branch `main`** (`refs/heads/main`). The command is `python3 h-mad/scripts/h_mad_phase7_integrate.py --feature gate-non-py-production-files --base main --route merge`, run first without `--apply`. `h_mad_phase7_integrate.py` accepts a base only when `git rev-parse --verify --quiet refs/heads/<name>` succeeds, so `origin/main` is refused (its docstring names that case).

This design does not assert how `main` relates to this branch, because `main` is shared with other lanes and can move before Phase 7. The script's `identity=` token decides at integration time. It compares local `main` with the feature branch, and `identity=y` needs `main` to hold no commit the branch lacks; how `main` relates to `origin/main` is not an input.

- **`identity=y`.** The merged tree is byte-identical to the branch tip, so the branch-tip suite run covers it.
- **`identity=n`.** The merged tree is new and needs the suite.

`--apply` still carries `--suite "python3.11 -m pytest"` unconditionally, because the script runs that command only when the merged tree differs from the branch tip. The `MERGED` line re-derives identity from the real trees and settles the question: if `main` moves between the plan and the apply, a planned `identity=y` becomes `identity=n` and the suite runs. The apply prints one of these:

- `identity=y suite=covered`: the suite was not run.
- `identity=n suite=PASS rc=0`: the suite passed on the merged tree.
- `identity=n suite=FAIL rc=<exit code or exception name>`: do not push.

`suite=unrun` appears only when `--suite` is omitted, which this design's apply never does.

`identity=` is printed only on `PLANNED` and `MERGED`. A `BLOCKED` line has no such token and says nothing about the suite. `git worktree list --porcelain` shows `refs/heads/main` checked out at `/Users/kimhawk/orca/skills`, another lane's tree that this feature never writes. `worktree_holding` in the script reports that, so the command above, run from this feature's worktree with a clean tree, prints `BLOCKED reason=base_checked_out_elsewhere:<path>`. The token therefore comes from running in the worktree that holds `main`, with `--branch BrightGold70/gate-non-py-production-files` added; without it the branch defaults to `main` and the line reads `BLOCKED reason=base_is_the_feature_branch:main`. The apply step is taken only on the operator's go-ahead in that worktree when it is clean; until then the plan output is the Phase-7 record.

The replay base (`git merge-base HEAD origin/main`) and the integration target (local `main`) are different refs by design. The base says what shipped before; the target says where this lands.

## Components Changed / Added
| Component | File path | Change type | Purpose |
|---|---|---|---|
| Task parser, wire-pin 5b | `h-mad/scripts/h_mad_wire_pin_gate.py` | modify | FR-1 widen `production`; FR-2 retire `ungated` |
| Judge | `h-mad/scripts/h_mad_tdd_judge.py` | modify | `_match_plans`, `PlanMatch`, `Listing`, `listing`, `listing` CLI verb, `target_module_names` non-`.py` guard |
| Target identity | `h-mad/scripts/h_mad_target_identity.py` | modify | `DOC_DATA_SUFFIXES`, `has_doc_data_suffix`, `is_doc_data`, `emit_doc_data`, `_is_exempt_location` |
| Claude gate | `h-mad/hooks/h-mad-tdd-gate.sh` | modify | `# M:H11` tail, docdata split, `# M:H-DOCDATA`, `_read_listing`, code-like branch |
| codex gate | `h-mad/hooks/h-mad-codex-tdd-gate.py` | modify | doc/data skip, `_judge_listed`, new call site |
| agy gate | `h-mad/hooks/h-mad-agy-tdd-gate.py` | modify | doc/data skip, inline listed block, new call site |
| Prose | `h-mad/references/codex-implementer-prompt.md`, `h-mad/references/codex-runtime.md`, `h-mad/references/phase5-substeps.md`, `h-mad/references/helper-scripts.md` | modify | FR-10 surfaces 1–4; `listing` verb documented |
| Parser tests | `h-mad/tests/test_h_mad_parse_tasks_non_py.py` | new | AC-1.1, AC-1.3, AC-1.4, AC-1.5 unit cases; the consumer-level CLI tests of §FR-1 |
| Wire-pin tests | `h-mad/tests/test_h_mad_wire_pin_gate.py` | modify | retire six `…ungated…` tests; AC-2.1–AC-2.4 |
| Doc/data tests | `h-mad/tests/test_h_mad_doc_data.py` | new | predicate, nine-suffix pin, parity of `_is_exempt_location` |
| Listing tests | `h-mad/tests/test_h_mad_tdd_judge_listing.py` | new | `listing`, CLI values, FR-4, FR-8 judge side, AC-3.5 judge side |
| Gate fixture support | `h-mad/tests/non_py_gate_support.py` | new | builds spec fixture R, selection fixture, mixed-plan fixture, newline-name fixture, AC-11.3/11.4 variants; `.venv` for listed-failing rows; `claude_author_env`, `default_authorship_env`, `assert_authorship`, `skip_unless_case_insensitive`; per-host real-entry drivers |
| Per-host gate tests | `h-mad/tests/test_h_mad_tdd_gate_non_py.py`, `h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py`, `h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py` | new | AC-3.x, FR-5–FR-8, FR-11 per host; NFR count (Claude) |
| Existing tests touched | `h-mad/tests/test_h_mad_target_identity.py`, `h-mad/tests/test_h_mad_tdd_gate_judge.py`, `h-mad/tests/test_h_mad_tdd_gate_docs.py` | modify | R13 marker; stub identity modules gain `emit_doc_data`; AC-10.1, AC-10.2, AC-10.3, judge-registration tokens |
| Mutation specs | `h-mad/tests/mutation-specs/wire_pin_ungated.json` (modify); `parse_tasks_non_py.json`, `doc_data_definition.json`, `listing_matcher.json`, `listing_connections.json`, `judge_non_py.json`, `claude_gate_listing.json`, `codex_gate_listing.json`, `agy_gate_listing.json`, `fr9_drive_refusals.json` (new); `claude_gate_judge_wiring.json` (re-anchor `H11`, `CG-CANON`) | modify / new | AC-9.3, AC-2.4, AC-3.1, AC-11.6 |
| FR-9 driver and evidence | `docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py`, `docs/03-analysis/probes/gate-non-py-production-files/fr9/` | new | AC-9.1, AC-9.2, AC-9.4, AC-9.5 |
| FR-9 driver refusal tests | `h-mad/tests/test_h_mad_fr9_drive_refusals.py` | new | one node per driver refusal (§FR-9 "Refusals") |

## Implementation Order
Every Task is test-first: its listed tests are run and seen RED, for the reason named, before the production edit. Controls and preservation tests are green before the edit and are named as such. After the GREEN edit:
- run the full suite, bare `python3.11 -m pytest` from PROJECT_ROOT, read on its summary line via `rtk proxy`;
- run the Task's mutation specs through `h-mad/scripts/h_mad_mutation_harness.py`, read on the `MUTATION:` token;
- run `h_mad_mutation_harness.py --check-anchors` over every spec in `h-mad/tests/mutation-specs/` that names an edited file, and require `ANCHORS: ANCHORS_OK`.

1. **Task 1 — parser and wire-pin (FR-1, FR-2).** Production: `h-mad/scripts/h_mad_wire_pin_gate.py`. Tests: `h-mad/tests/test_h_mad_parse_tasks_non_py.py`, `h-mad/tests/test_h_mad_wire_pin_gate.py`.
   - RED: AC-1.1 fails with `production == ['h-mad/scripts/a.py']`, AC-2.2 fails on the present key, and the §FR-1 consumer tests read as that section states.
   - Specs: `wire_pin_ungated.json` (U1 and U2 re-pointed, U3–U5 retired) and `parse_tasks_non_py.json` (the `key == "production"` guard → AC-1.4; `# M:P-NONPY` → AC-1.1).
   - Plan M5 and M12's parser probe read the `ungated` key and must not be re-run after this Task.
2. **Task 2 — doc/data definition and exempt-location helper (FR-11 definition).** Production: `h-mad/scripts/h_mad_target_identity.py`. Tests: `h-mad/tests/test_h_mad_doc_data.py`.
   - RED: the module fails at import on `DOC_DATA_SUFFIXES`. That import error is not accepted as the RED reason by itself: the Task first adds the names as stubs (an empty tuple, predicates returning `False`), and the nine-suffix pin (`test_doc_data_suffixes_are_the_spec_nine`, which pins `DOC_DATA_SUFFIXES` to the spec's nine strings in order) and the predicate cases must then fail by assertion before the real definitions are written.
   - Spec: `doc_data_definition.json` predicate mutants. A case-sensitive compare is killed by the upper-case case. `any` in place of `all` is killed by the mixed-names case. `Path.suffix` in place of end-of-basename is killed by the dotfile `.md` case, the mutant's own test node. `python3 -c 'from pathlib import Path; print(repr(Path(".md").suffix), repr(Path("a.tar.md").suffix))'` prints `'' '.md'`, so `a.tar.md` reads the same under both rules: it stays a predicate case and kills nothing here.
3. **Task 3 — the judge (FR-3 judge side, FR-4, FR-8 judge side).** Production: `h-mad/scripts/h_mad_tdd_judge.py`. Tests: `h-mad/tests/test_h_mad_tdd_judge_listing.py`.
   - RED: `AttributeError` on `listing`, plus assertion failures for the CLI value table and for AC-4.5 (`target_module_names` returns `{'scripts.tool', 'tool'}` today, per spec §(c)).
   - Tests write their own plan files (§Test Strategy, unit tier); they do not import `non_py_gate_support`, which arrives in Task 4.
   - Specs: `listing_matcher.json` judge-level entries (`# M:L-SELECT`, `# M:L-UNREADABLE`, listed-outranks-unreadable, any-name) and `judge_non_py.json` (`# M:K-IMPORT-NONPY`). The listed-outranks-unreadable mutant replaces the line `if listed:  # M:L-LISTED` with `if listed and not any(m.status == "unreadable" for _, plans in per_name for m in plans):  # M:L-LISTED`, and `test_listing_listed_outranks_an_unreadable_sibling` kills it. `test_listing_unreadable_when_no_plan_lists_the_target` kills the removal of the `# M:L-UNREADABLE` arm.
   - The existing `tdd_judge_resolution.json` and `tdd_judge_wiring.json` must stay `ALL_CAUGHT`; that is the `.py` identity proof.
4. **Task 4 — codex gate (FR-6, FR-8, FR-11 codex).** Production: `h-mad/hooks/h-mad-codex-tdd-gate.py`. Tests: `h-mad/tests/non_py_gate_support.py` (new; it is test support, so `_dir_match` exempts it) and `h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py`.
   - RED: AC-6.1 reads ALLOW where DENY is expected.
   - Specs: `codex_gate_listing.json` (doc/data skip, exempt check, chain-unreadable deny, listing-unreadable deny), the codex rows of `listing_connections.json`, the codex entries of `listing_matcher.json` (callee, selection), and the codex entries of `doc_data_definition.json` (nine per-suffix mutants, AC-11.6).
   - Preservation: `test_codex_directory_target_is_skipped` is green before and after. Removing `# M:CX-DOCDATA` kills it, because `_judge_listed` then raises `IndexError` on `names[0]`, which reaches `# M:G2` as `kind=judge-error`.
5. **Task 5 — agy gate (FR-7, FR-8, FR-11 agy).** Production: `h-mad/hooks/h-mad-agy-tdd-gate.py`. Tests: `h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py`.
   - RED: `test_agy_listed_absent_test_denies` (AC-7.1) and `test_agy_listed_beside_unreadable_absent_test_denies` read `{"decision": "allow"}` where a deny is expected.
   - Specs: `agy_gate_listing.json` and the agy rows and entries of the three shared specs. `agy_tdd_gate.json` must stay `ANCHORS_OK`.
6. **Task 6 — Claude gate (FR-5, FR-8, FR-11 Claude, NFR).** Production: `h-mad/hooks/h-mad-tdd-gate.sh`. Tests: `h-mad/tests/test_h_mad_tdd_gate_non_py.py`, and the modified `h-mad/tests/test_h_mad_target_identity.py` (R13) and `h-mad/tests/test_h_mad_tdd_gate_judge.py`.
   - RED: `test_claude_listed_absent_test_denies` (AC-5.1) and `test_claude_listed_beside_unreadable_absent_test_denies` read ALLOW where DENY is expected, with `assert_authorship` passing, so the failure is the verdict and not the arrangement. `test_claude_unlisted_beside_unreadable_is_judge_error` reads ALLOW too; it is unasserted, as an "Either" state.
   - The two stub `h_mad_target_identity.py` modules gain `def emit_doc_data(record): print('docdata no')`. Provenance: a stub models the module the hook imports, and the hook now imports one more name. No assertion changes.
   - Specs: `claude_gate_listing.json` (`# M:H-DOCDATA`, `# M:H-LIST-RC`, `# M:H-LIST-NAME`, `# M:H-LIST-INROOT`, `# M:H-LIST-UNREADABLE`, `# M:H-LIST-DECODE`, `# M:H-LIST-CONTEXT`, the zero/several-lines guard, the docdata-line guard, and `W7R` and `W7F` on the `# M:W7` launch), the Claude rows and entries of the shared specs, and the re-anchored `H11` and `CG-CANON` in `claude_gate_judge_wiring.json`. The re-anchored mutants keep `;emit_canon(i);emit_doc_data(i)`-shaped tails, so they still run.
   - `# M:H-LIST-UNREADABLE`: removing the arm falls through to "Anything else", which is also `judge-error`, so a kind alone cannot kill it. `test_claude_unreadable_plan_is_judge_error` (AC-8.1) also asserts the reason contains `listing is undecidable`. `# M:H-LIST-DECODE`: the mutant restores `LISTED_TARGET=$(_pct_decode "${BASH_REMATCH[1]}")`, and `test_claude_listed_symlink_to_a_newline_name[failing]` kills it (§Test Strategy).
   - Preservation: `test_claude_directory_stays_judge_error_where_state_may_exist` and `test_claude_directory_allows_where_no_state_can_exist` pin today's verdicts (§"A directory target, today"). They are green before and after, so there is no RED to see. A `claude_gate_listing.json` mutant supplies the discrimination: it prefixes the unmarked line `_chain_may_hold_state "$ROOT_ABS" "$TARGET_PATH" || _allow` with `[ "$DOC_DATA" = yes ] && _allow; `, the new allow path this design forbids, and the first test kills it. The first test skips when `/bin/bash` is not 3.2, on the residual §D13 states.
7. **Task 7 — prose (FR-10).** Production: the four reference files in §FR-10. Tests: `h-mad/tests/test_h_mad_tdd_gate_docs.py`.
   - RED: AC-10.1 on each of its eight nodes (§FR-10 pre-change hits); AC-10.2 on any of its eleven tokens (plan M9: 0 matching lines each); AC-10.3 on anchor count 0; the registration test on `TDD-LISTING:`.
   - After the edit, `test_gate_prose_has_no_retired_phrasing` is green on all eight nodes, and the §Test Plan sweep prints nothing.
8. **Task 8 — end-to-end proof and the whole mutation run (FR-9).** Production: `docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py`, plus its evidence. Tests: `h-mad/tests/test_h_mad_fr9_drive_refusals.py`.
   - RED: the Task first writes the driver as an argument parser that prints nothing and exits 0. Each of the nine nodes then fails on the missing token line, not on a missing file. The FR-9 verdict rows have no RED: they are measurements, read from `FR9-DRIVE:`.
   - Run order: the fixture scenario on each host; then the replay, before then after, on each host. All of it runs before the Phase 7 push (§FR-9).
   - Then the harness over every spec named above plus `wire_pin_ungated.json` and `fr9_drive_refusals.json`, requiring `MUTATION: ALL_CAUGHT` with `refused=0`.

The order is codex, then agy, then Claude, because the two in-process hosts exercise `listing` with no transport in between. If they go first, a CLI-only defect cannot be mistaken for a matcher defect.

## Data Model / Schema Changes
- **Task dict** (`_parse_tasks`). The `ungated` key is removed. `production: list[str]` now holds non-`.py` path tokens too (doc/data tokens included); `.py` tokens come first per line. All other keys are unchanged (AC-1.5).
- **`check()` result.** The `ungated` key is removed.
- **New judge types.** `PlanMatch` and `Listing` (§D4).
- **CANON exchange** between the Claude gate and the `# M:H11` process. One trailing line, `docdata yes|no`, follows the unchanged `CANON 1` record. `emit_canon` and the `CANON 1` grammar are unchanged.
- **No change** to `.bkit-memory.json`, `.h-mad/wires.jsonl` or the impl-plan grammar.

## API / Interface Changes
- `h_mad_tdd_judge.listing(root: Path, names: Sequence[Path], records: Sequence[Record]) -> Listing`. This is the FR-3 function all three hosts call.
- `h_mad_tdd_judge._match_plans(root: Path, target: Path, records: Sequence[Record]) -> Tuple[PlanMatch, ...]`. Private, shared by `resolve` and `listing`.
- CLI: `h_mad_tdd_judge.py listing --root DIR --name PATH [--name PATH ...]` → exactly one `TDD-LISTING:` line from the value set `listed target=…`, `not-listed` and `unreadable file=… error=…`; exit 0, or 2 on an internal exception (§D4 table).
- `h_mad_target_identity`: `DOC_DATA_SUFFIXES: tuple[str, ...]`, `has_doc_data_suffix(name: str) -> bool`, `is_doc_data(names: Sequence[str]) -> bool`, `emit_doc_data(identity: Identity) -> None`, `_is_exempt_location(relative: str) -> bool`.
- `h-mad-codex-tdd-gate.py`: module-level `_judge_listed(root: Path, resolved: Identity) -> str`.
- Wire-pin CLI: the `  ungated: …` detail lines are no longer printed. `WIREPIN:` is unchanged.

## Error Handling Strategy
- **Fail-closed kinds.** Every undecidable listing on a code-like, non-exempt target is `kind=judge-error`, on every host:
  - chain unreadable: `listing` verb `unreadable` (Claude), or `read_chain` `unreadable` (codex, agy);
  - an active record's impl-plan raising `OSError` or `UnicodeDecodeError`, when no readable plan lists a name: `Listing.value == "unreadable"`.
  A name that a readable plan lists is decided, so it is judged beside an unreadable plan (§D4; spec R-D). An absent impl-plan is `not-listed`. A doc/data target never reaches either decision (spec FR-8, AC-8.4).
- **Claude transport.** It refuses `judge-error` on each of: zero or several lines, `rc != 0`, an unrecognised line, a `listed target=` naming a path the gate did not pass, and a missing or malformed `docdata` line. A crash of the `# M:H11` process exits through `set -e` into `_on_exit` (`# M:T2`), which is already `judge-error`.
- **In-process hosts.** An exception in `_judge_listed` reaches codex's `# M:G2` handler as `kind=judge-error`. An exception in agy's block leaves `decision` as `None`, and the `finally` emits the existing `Gate could not reach a judgement. kind=judge-error`.
- **The verb's own exit codes.** `listing` exits 0 on every normal verdict and 2 only for an internal exception, with stderr and an empty stdout. The Claude gate treats rc 2 as `judge-error`. This follows the base invariant §"Audit-gate signal discipline" (token on stdout, exit 0 on a verdict).
- **FR-9 driver.** It prints an `FR9-DRIVE:` token with exit 0 on PASS or FAIL, and exit 2 with `FR9-DRIVE: UNREADABLE <why>` for each of the nine refusals in §FR-9 "Refusals".

## Test Strategy
- **Unit tier.** No mocks. This covers `_parse_tasks`, `is_doc_data` and `_is_exempt_location`, and `listing`/`_match_plans`/`target_module_names` driven over real temp files: plans written as real files, invalid UTF-8 written as bytes, and unparsable `.bkit-memory.json`. `test_h_mad_tdd_judge_listing.py` writes these itself. Parser unit tests are supplementary to the consumer-level tests in §FR-1.
- **Host tier.**
  - **Real entry points.** Each host's hook file runs by its worktree path, through its real stdin entry point: `/bin/bash` for Claude, `python3` for codex and agy. The environment is `tdd_gate_support.hermetic_env`, and the scratch repos are built by `non_py_gate_support.py` exactly to spec §"Fixture" and to the AC-6.5 selection fixture (states S1 and S2). Each also gets `<root>/.agents`, agy's cwd, as `test_h_mad_agy_tdd_gate.py`'s fixture does. Every case with a listed target and a failing test also gets `tdd_gate_support.build_venv(root / ".venv", with_pytest=True)`, so its ALLOW does not depend on the `python3` on `PATH` (§FR-9 "Interpreter" holds the reading).
  - **Claude authorship.** Spec §"Fixture" names the arrangements and which criterion uses which. Building the environment and checking it are separate:
    - `non_py_gate_support.claude_author_env(**extra)` returns `hermetic_env(HMAD_CODEX_UNAVAILABLE="1", HMAD_AGY_UNAVAILABLE="1", **extra)`. Every Claude-host case uses it except AC-5.5, including the "Either" rows, so one environment serves them all.
    - `default_authorship_env(bin_dir)` is AC-5.5's: `hermetic_env` with `HMAD_AGY_UNAVAILABLE` removed and a stub `codex` first on `PATH`. The removal is explicit because `DROPPED_ENV` holds `HMAD_CODEX_UNAVAILABLE` but not `HMAD_AGY_UNAVAILABLE`.
    - `assert_authorship(env, root, key, expected=CLAUDE_AUTHOR_LINE)` runs `python3 <judge> implementer --root <root> --feature <key>` under `env`, and asserts the whole stdout line equals `expected`. AC-5.5 passes `DEFAULT_AUTHOR_LINE`. Both lines are the ones spec §"Fixture" requires.
    - It is called, before the hook, only for the spec's Claude-author and Default rows, and for the judged tests below that no spec row names: listed beside an unreadable plan, and the newline-ending name. Both use key `f`. It is not called for the "Either" rows, where the line can be `no-record` or `unreadable` (spec §"Fixture"), nor for the directory preservation tests or the NFR count, which read no authorship.
  - **Listed beside an unreadable plan (FR-8, spec R-D).** Records `f` and `g` are both active, and `scripts/hard.sh` is a hard link to `scripts/tool.sh`. `f.impl-plan.md` lists `scripts/tool.sh` with `tests/test_tool.py`. `g.impl-plan.md` holds invalid UTF-8 bytes.
    - Unit, writing its own plan files: `test_listing_listed_outranks_an_unreadable_sibling` expects `Listing("listed", <scripts/tool.sh>, None, "")` for both names. `test_listing_unreadable_when_no_plan_lists_the_target`, with `f`'s plan listing another file, expects `Listing("unreadable", None, <g's plan>, "UnicodeDecodeError")`.
    - Host, built by `non_py_gate_support`, each writing `scripts/tool.sh`: `test_claude_listed_beside_unreadable_failing_test_allows` is ALLOW; `test_claude_listed_beside_unreadable_absent_test_denies` is DENY `kind=test-missing`; and the control `test_claude_unlisted_beside_unreadable_is_judge_error`, where no plan lists it and `g`'s is unreadable, is DENY `kind=judge-error`. Each has `test_codex_` and `test_agy_` twins.
  - **Newline-ending name.** `scripts/alias.sh` is a symlink to `scripts/tool\n`, a name ending in a newline. `f.impl-plan.md` lists `scripts/alias.sh` with `tests/test_tool.py`, and the write spells `scripts/alias.sh`. `test_claude_listed_symlink_to_a_newline_name` and its `test_codex_` and `test_agy_` twins take two parameters: `failing` is ALLOW, and `absent` is DENY `kind=test-missing`. Reading at `09a309ca` on a scratch prototype of this design, deleted after the run: both rows and the three rows above read as stated on all three hosts. With `$(_pct_decode …)` in place of `_pct_capture`, Claude's `failing` and `absent` both read `kind=judge-error`.
  - **One host per file.** Each host has its own test file, so every mutant's scoring command runs that host alone (spec AC-3.1, AC-11.6).
  - **One case per member.** AC-11.3 and AC-11.4 are parametrised, one case per member, with ids equal to the member, so a per-suffix mutant names one node.
- **Process count (NFR).** `tdd_gate_support.marker_shim` is placed first on `PATH` as `python3`, so it logs every launch, and the test counts launches per write. Expected counts:
  - doc/data write with state: 2 (reader and canonicalise; 0 extra);
  - unlisted code-like write with state: 4 (2 extra, at most 3 allowed);
  - unlisted code-like write without state: 2.
  A control on the base-commit hook gives 2 for the unlisted `.sh`.
- **Case folding.** `tdd_gate_support.assert_case_insensitive` asserts and never skips, and `test_case_insensitive_precondition_is_asserted` pins that, so neither is touched. AC-3.3's cases and AC-11.2's `R/changes.md` case call a new `non_py_gate_support.skip_unless_case_insensitive(directory)` first. It touches a probe file, and calls `pytest.skip` when the opposite-case spelling does not exist. `test_skip_unless_case_insensitive_skips_on_a_case_sensitive_volume` has three arms, because the forced-`False` arm alone passes on a helper that always skips: the real volume, read by the test's own probe (returns where the volume folds, skips where it does not); `os.path.exists` forced `True` (must return); and `os.path.exists` forced `False` (must skip). Residual: on a case-sensitive volume these nodes report as skipped, a mutant scored on them is not killed there, and the skip count in the summary line is the signal.
- **Mutation tier.** Every new guard has at least one entry (§Implementation Order). Python-file entries carry a `symbol` key, so a migrated anchor is refused rather than mis-scored. Results are read from the `MUTATION:` token, never `$?`.
- **Documentation tier.** `test_h_mad_tdd_gate_docs.py` pins the prose. `test_gate_prose_has_no_retired_phrasing` is new, with one parametrised node per §FR-10 branch, so a healthy branch cannot cover a sick one. Each node runs `git -C <repo root> grep -n -E <branch> -- h-mad/SKILL.md h-mad/references h-mad/agents h-mad/invariants.base.md` on the real corpus and asserts exit 1 with empty stdout, so a `git grep` error (128) fails rather than passes. RED: at `09a309ca` all eight nodes fail, on 7 matching lines in 3 files holding 9 occurrences (`git grep -o -h -E <branch> -- <same pathspecs> | wc -l`: 1, 1, 1, 1, 1, 1, 2, 1). The test file is outside the corpus, so its own needles cannot score. Residual: §FR-10's, a phrasing split across a hard wrap.
- **Live tier.** The FR-9 driver. Its refusals are tested in `test_h_mad_fr9_drive_refusals.py` (§FR-9 "Refusals").

## Test Plan
- `python3.11 -m pytest h-mad/tests/test_h_mad_parse_tasks_non_py.py h-mad/tests/test_h_mad_wire_pin_gate.py h-mad/tests/test_h_mad_parse_tasks_paths.py -q`: FR-1, FR-2. The six existing `test_h_mad_parse_tasks_paths.py` tests named by AC-1.2 are unmodified.
- `python3.11 -m pytest h-mad/tests/test_h_mad_doc_data.py h-mad/tests/test_h_mad_target_identity.py -q`: D13, R13.
- `python3.11 -m pytest h-mad/tests/test_h_mad_tdd_judge_listing.py h-mad/tests/test_h_mad_tdd_judge.py -q`: D4, FR-4. The existing `M:K-IMPORT-*` tests are unmodified (AC-4.5).
- `python3.11 -m pytest h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py -q`, `… test_h_mad_agy_tdd_gate_non_py.py -q` and `… test_h_mad_tdd_gate_non_py.py -q`: each host alone.
- `python3.11 -m pytest h-mad/tests/test_h_mad_tdd_gate_docs.py -q`: FR-10, including AC-10.1's phrase sweep.
- `python3.11 -m pytest h-mad/tests/test_h_mad_fr9_drive_refusals.py -q`: the FR-9 driver's refusals.
- `git grep -n -E 'production-Python|a .\.py. suffix in any case|never gated|only production|production-.\.py.|markdown / yaml|Both gates|neither gate' -- h-mad/SKILL.md h-mad/references h-mad/agents h-mad/invariants.base.md`: must print no line after Task 7.
- `python3 h-mad/scripts/h_mad_mutation_harness.py <spec>` for each spec in §Components. Read `MUTATION:`.
- `python3.11 -I docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py …` per scenario, side and host. Read `FR9-DRIVE:`.
- Full suite per Task: `rtk proxy python3.11 -m pytest`, scored on the summary line.

## Test Boundaries
| Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |
|---|---|---|---|---|
| `h_mad_tdd_judge.py judge` CLI and `h_mad_wire_pin_gate.py` CLI, over the real `_parse_tasks` | AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5 | spec FR-1 AC inputs; verdicts and stdout stated in §FR-1 "Consumer-level coverage". Supplementary: parser unit tests of the spec's expected lists, and the six named `test_h_mad_parse_tasks_paths.py` tests unmodified | none | gate verdicts (host rows) |
| `h_mad_wire_pin_gate.check` and `main` CLI | AC-2.1, AC-2.2, AC-2.3 | spec FR-2 AC text: first line `WIREPIN: PASS tasks=1 wiring=0 unpinned=0 mislabeled=0`, no `ungated:` line, no `ungated` key, `UNSHAPED` kept | none | judge behaviour |
| `h_mad_mutation_harness.py` over `wire_pin_ungated.json` | AC-2.4 | `MUTATION: ALL_CAUGHT` token with `refused=0` | none | other specs |
| `h_mad_tdd_judge.listing` via codex, agy and Claude entry points | AC-3.1 | spec AC-3.1: callee mutant flips AC-5.1, AC-6.1, AC-7.1 to ALLOW; six connection mutants in §AC-3.1 table, scored by `MUTATION:` token | none | matcher internals (unit rows) |
| `h-mad-codex-tdd-gate.py`, `h-mad-agy-tdd-gate.py`, `h-mad-tdd-gate.sh` real stdin entry points | AC-3.2, AC-3.3, AC-3.4 | spec fixture plus symlink, case-fold and hard-link variants; expected DENY `kind=test-missing` from spec text | none | case-sensitive volumes (AC-3.3 skips through `skip_unless_case_insensitive`) |
| same three hook entry points and `h_mad_tdd_judge.listing` | AC-3.5 | spec AC-3.5 list of three residual spellings, each expected ALLOW | none | closing the residuals (out of scope) |
| `h_mad_tdd_judge.judge` and `target_module_names` | AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | spec FR-4 AC verdict tuples and `frozenset()` expectations | none | gate transport |
| `h-mad-tdd-gate.sh` real stdin entry point under `/bin/bash` | AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6, AC-5.7, AC-5.8 | spec FR-5 AC verdicts on spec fixture and AC-6.5 selection fixture states S1 and S2, each under spec §"Fixture"'s named arrangement | a stub `codex` on `PATH`, for AC-5.5 only | codex and agy hosts |
| `h-mad-codex-tdd-gate.py` real stdin entry point | AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5 | spec FR-6 AC verdicts on spec fixture and selection fixture | none | Claude and agy hosts |
| `h-mad-agy-tdd-gate.py` real stdin entry point | AC-7.1, AC-7.2, AC-7.3, AC-7.4 | spec FR-7 AC verdicts in agy `{"decision": …}` form | none | T1–T5 checks (existing tests) |
| all three hook entry points | AC-8.1, AC-8.2, AC-8.3, AC-8.4 | spec FR-8 AC states (invalid UTF-8 plan, unparsable state, absent plan) and expected `judge-error` or ALLOW; spec FR-8's R-D paragraph over the §Test Strategy two-record fixture | none | `.py` path behaviour |
| verified by: live-run | AC-9.1, AC-9.2 | `docs/03-analysis/probes/gate-non-py-production-files/fr9/` readings.tsv, hook.json and implementer.txt, token `FR9-DRIVE: PASS` | none | mutation scoring |
| verified by: live-run | AC-9.3 | `MUTATION: ALL_CAUGHT` over every spec in §Components, `refused=0` | none | end-to-end readings |
| verified by: live-run | AC-9.4, AC-9.5 | `docs/03-analysis/probes/gate-non-py-production-files/fr9/` provenance.json and readings.tsv against spec AC-9.4 table, token `FR9-DRIVE: PASS` | none | synthetic fixture rows |
| `test_h_mad_tdd_gate_docs.py::test_gate_prose_has_no_retired_phrasing` over the real prose corpus | AC-10.1 | spec AC-10.1's five branches and §FR-10's three added branches, each asserting `git grep` exit 1 and empty stdout; pre-change hits in §FR-10 | none | wrapped phrasings (stated residual) |
| `test_h_mad_tdd_gate_docs.py::test_hook_bullets_state_the_shipped_rule` and `::test_skill_states_the_docs_first_component_rule` | AC-10.2, AC-10.3 | spec AC-10.2 eleven tokens; spec AC-10.3 anchor-count and five-token list | none | prose outside the four surfaces |
| all three hook entry points | AC-11.1, AC-11.2, AC-11.3, AC-11.4, AC-11.5 | spec FR-11 AC lists (nine suffixes, seven excluded members, mixed hard links), one case per member | none | judge internals; AC-11.2's `R/changes.md` case on a case-sensitive volume (skips) |
| `h_mad_target_identity.is_doc_data` and `h_mad_mutation_harness.py` over `doc_data_definition.json` | AC-11.6 | spec AC-11.6: each removed suffix flips its AC-11.3 case on each host, scored by `MUTATION:` token | none | a bash copy of the definition (none exists, spec FR-11) |

## Invariant Compliance
- **Audit-gate signal discipline.** Complies. `TDD-LISTING:` and `FR9-DRIVE:` are stdout tokens with exit 0 on every verdict. Non-zero is used only for internal errors or unreadable input.
- **Single-source contract.**
  - Complies for listing: one `_match_plans` and one `listing`, called by all three hosts.
  - Complies for doc/data: one `is_doc_data`, used by all three hosts (no copy).
  - The exempt-location rule is applied by `_is_production_python` (unchanged) and by `_is_exempt_location` (new). The parity test is the byte-equivalence alternative this invariant allows. Claude's bash `_dir_match` and `# M:H-DOCS` predate this feature, and so does their two-implementation shape.
- **Standalone / no plugin dependency; No new external dependency.** Complies: stdlib Python, `/bin/bash`, `git` and `tar`. The FR-9 driver calls no agent CLI and does not run the `verify-hmad-gates` helper.
- **Portable time bounds.** Complies: no `timeout`/`gtimeout`. The judge keeps its own bounded runner.
- **Doc-template superset compliance.** Complies. This document carries every Phase-4 template section, and `h_mad_doc_shape_check.py` is run on it.
- **Operator-override preservation; Backward compatibility (audit gate).** Not touched by this feature.
- **Marker discipline.** Not applicable: no orchestrator transition changes.
- **Mutation verification.** Complies: harness landing check plus a `symbol` key on Python entries; the FR-9 driver re-reads the copied plan (`git hash-object`) and the executed hook blob.
- **Test discrimination.** Each new test has a named RED reason or is named as a control or preservation test (§Implementation Order, §FR-1, §Test Strategy). Each connection has both directions (§AC-3.1).
- **Verifying a review finding.** Applied to P5-1, P5-2, PF-1 and PF-2, each re-run (report).
- **Guard narrowing.** The doc/data allow keeps an existing ALLOW (spec NFR Security). The only narrowing direction is ALLOW → judged.
- **Connection enforcement.** Complies: six connection mutants, two per host (§AC-3.1).
- **Incident replay.** Complies: the real Task, byte-for-byte, before and after (§FR-9).
- **Assumption verification; Behavioural premises carry their command.** Every tree premise carries its command (§"Tree premises", §FR-10, §Phase 7). The bash 3.2 constructs were executed under `/bin/bash` 3.2.57 (§"The bash 3.2 constructs").
- **Counts a dispatch reports.** Every count here was re-derived by the command beside it.
- **Wrapper–runtime reconciliation.** Not applicable: no external runtime wrapper.
- **Regression provenance.** Stated for each existing test this feature changes:
  - the six `…ungated…` tests and U3–U5: stale contract;
  - the `*.md|*.yaml` marker: site removed;
  - the stub identity modules: model update, no assertion changed;
  - `test_skill_states_the_docs_first_component_rule`: spec FR-10 provenance, adopted.
- **Both halves of a doc change.** Complies: every prose removal lands with the shipped rule and its pins in the same Task.
- **Reimplementation parity.** Not applicable.
- **Project: Skill self-containment; Skill manifest integrity.** Complies: no cross-skill import. `SKILL.md`'s rule text changes through the split reference `phase5-substeps.md`, and its frontmatter is untouched.

## Risks (Phase-5 notes carried and re-verified)
- **P5-1.** The Claude force mutant's `scripts/other.sh` control asserts DENY, not a kind (§AC-3.1 table).
- **P5-2.** The judge's runtime closure includes `h_mad_state_write`. Verified with `grep -n 'import h_mad_state_write' h-mad/scripts/h_mad_tdd_judge.py`: one lazy import, inside `main`'s `implementer --record` branch. Its own imports (`h_mad_bkit_guard`, `h_mad_state_ownership`, `h_mad_state_validate`) are at module level in `h-mad/scripts/h_mad_state_write.py`. The before tree takes all of `h-mad/`, so this is covered.
- **PF-1.** `h_mad_wire_registry` imports `h_mad_assemble_tdd` at runtime, only inside its `register` CLI branch (`from h_mad_assemble_tdd import misrooted_candidates`). That is not on any gate's path, and the before tree covers it.
- **PF-2.** `grep -c 'h_mad_mutation_harness.py' h-mad/scripts/h_mad_target_identity.py` prints 2 matching lines: the `SAFE_HMAD_SCRIPT_OPTIONS` key and the `script.name == "h_mad_mutation_harness.py"` comparison in `_safe_hmad_script`. No line imports it. The spec's "only as a string in its safe-command table" undercounts the places; its conclusion (not imported) holds.
- **Stub-tree breakage.** Task 6 updates both stub identity modules in `test_h_mad_tdd_gate_judge.py`. Any other stub that writes an `h_mad_target_identity.py` without `emit_doc_data` makes the Claude gate refuse `judge-error`. Census command: `git grep -n 'def emit_canon' -- h-mad/tests` (2 matching lines today).
- **Interpreter for FR-9.** See §FR-9 "Interpreter".

## Version History
- v1.0: Initial design draft (2026-11-04), from spec v1.5 (cfe9781b) and plan v1.3 (4bf4ee4c). Names the listing decision's home (h_mad_tdd_judge._match_plans, shared by resolve and the new listing function), the listing CLI verb and its three TDD-LISTING values, the per-host new call sites and AC-3.1 connection sites, the doc/data definition in h_mad_target_identity used by all three hosts (Claude through the existing M:H11 canonicalise process; no bash copy), the shipped Claude-gate process count (2 extra where state exists), the FR-9 driver and replay mechanism, the widened FR-10 phrasing set (eight branches, zero added surfaces), and the Phase-7 integration target (local main via --base main). No audit cycle answered (first draft).
- v1.1: Operator-requested correction (2026-11-04); answers no audit cycle. §Phase 7 integration target (PF-3) no longer asserts how main relates to origin/main or to this branch, because main is shared and can move before Phase 7. The script's identity= token decides at integration time; --apply keeps --suite unconditionally. It now states the suite= token for each case, that BLOCKED carries no identity= token, and that the token comes from the worktree holding main with --branch. §FR-9's "Before tree (D14, R15)" bullet drops its present-tense reading of the replay base, which the driver re-derives at run time and records; the value is not pinned here.
- v1.2: Answers design audit cycle 1 (2026-11-04): gate-non-py-production-files.design.audit.v1.p1.md, gate-non-py-production-files.design.audit.v1.p2.md (only the items kept by gate-non-py-production-files.design.rejections.md) and gate-non-py-production-files.design.audit.v1.p3.unverified.md. p1 must 1: implementer=null does not make Claude the author; the driver and the tests use spec v1.8's Claude-author arrangement (both HMAD_*_UNAVAILABLE set) with a TDD-IMPLEMENTER check, and AC-5.5 alone keeps default authorship. p1 must 2: listing now returns unreadable when any plan of any name is unreadable, with a two-record mixed-plan test; resolve is unchanged. p1 must 3: the canonicalise, bash 3.2 and mutation-anchor probes carry runnable blocks and output, re-run at 3ff9ea4a; the census now names all five wire_pin_ungated mutants. p2 must 3 (kept half): _judge_listed step 6 binds relative from listed.selected. p3 must 1: the directory statement is corrected from a real-hook drive (Claude judge-error where state may exist, no new allow path) with preservation tests. p3 must 2: the nine-suffix pin belongs to Task 2 only. Should-fixes: the Path.suffix mutant is killed by the dotfile case; the FR-9 driver creates <root>/.agents; agy reaches is_doc_data through identity; spec and plan pointers refreshed, and the retired copy option is marked history; the replay commit is the base from git merge-base HEAD origin/main; the driver refuses the replay when base equals HEAD, so evidence is taken before the Phase 7 push.
- v1.3: Follows spec v1.9 (611c4bae, 2026-11-04), which adds AC-8.5 (mixed plans); answers no audit cycle. The AC-8 row of Test Boundaries gains AC-8.5, and the Test Strategy mixed-plan paragraph names it. The host tests now also run without scripts/hard.sh, because AC-8.5 states no hard link. The live spec pointer moves to v1.9, and the live plan pointer moves to v1.5 (6282cc9d).
- v1.4: Corrective revision (2026-11-04), not re-audited. Answers gate-non-py-production-files.design.audit.v2.p1.md musts 1-4 and the must-fix and should-fixes of docs/03-analysis/gate-non-py-production-files.design.delta-review.2e47388a.md, and applies operator ruling R-D (spec v1.10, bba8bfad; plan v1.6, 636a538f). R-D: listing's order is listed, then unreadable, then not-listed, with selected from readable plans only; the Task 3 mutant, test names, host tests and Error Handling follow, AC-8.5 is removed, and the residual is stated. p1 must 1: Claude decodes the listed target with _pct_capture, with a newline-ending-name regression on all three hosts. p1 must 2: assert_case_insensitive asserts, so AC-3.3 and AC-11.2's case-variant case use a new skip_unless_case_insensitive precheck. p1 must 3: FR-1's Test Boundaries row is now consumer-level, through the judge and wire-pin CLIs; wire-pin alone exposes no production, so the judge CLI carries AC-1.1 to AC-1.4. p1 must 4: AC-10.1 becomes test_gate_prose_has_no_retired_phrasing, eight nodes, RED at 09a309ca. Delta must: env-building and assert_authorship are separate, and Either rows are unasserted. Delta shoulds: Task 3 writes its own plan files; host fixtures and each driver scratch root get a .venv, verified on a .py control; eight driver refusals each get a node in test_h_mad_fr9_drive_refusals.py; RED lines for Tasks 5, 6 and 8. Nits: the Task 3 sentence, Claude's unreadable-arm mutant, and the no-before-side refusal.
- v1.5: Post-Phase-6 alignment (2026-11-06), following Phase 6 at 38dd84a6; not re-audited. It answers no audit cycle and moves the design to the verified tree, on operator-approved decisions from the Should-fix section of docs/03-analysis/gate-non-py-production-files.analysis.md. Driver refusals go from eight to nine: plan-absent-at-base gains a fixture, and the exit-1 residual now names only an uncaught exception such as a missing git. The realpath check is stated before the blob check. The plan-blob-mismatch fixture now states the repo-local core.autocrlf that the test uses, not GIT_CONFIG_* variables the driver would drop. The skip test is stated with its three arms. # M:H-LIST-CONTEXT is recorded with its host parity, and the note that the region after # M:H3 is unchanged now names that exception. fr9_drive_refusals.json joins Components and Task 8, and H-LIST-CONTEXT, W7R and W7F join Task 6's spec list. The document stated no mutation-row total before this revision and states none in its body now; reading at 38dd84a6: 102 rows across the feature's 10 specs, 15 of them in claude_gate_listing.json. The v1.4 entry keeps its eight as history.
