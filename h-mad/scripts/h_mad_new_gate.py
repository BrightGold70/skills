#!/usr/bin/env python3
"""h_mad_new_gate.py — scaffold a verdict-token gate with its invariants built in.

h-mad hand-rolls one shape over and over. Counted 2026-08-25 from the scripts
themselves: **20 distinct verdict tokens**, and 18 of the 20 share the same
contract — a `check()`-shaped function, a CLI printing
`TOKEN: <VERDICT> <counts>`, exit 0 on a verdict and 2 on a cannot-judge.

The code is not what costs time. Three invariants are, and each has been got
wrong at least once in this repo:

  1. **A cannot-judge carries NO counts.** `WIRING: UNKNOWN` omits `issues=`,
     `CTXBUDGET: UNKNOWN` omits `used=`, `EVIDENCE: UNREADABLE` omits its tool
     counts, `VERSION-HISTORY: REFUSED` omits `line=`. All for one reason: a
     zero is indistinguishable from "nothing was measured", and the zero reads
     as clean. `h_mad_do_preconditions.py` shipped the opposite — a heading-less
     report scored `must_count=0` and CLEARED the Phase-5 gate while the audit
     gate returned `INVALID` on the same file (#39).
  2. **Exit 0 on any verdict.** A FAIL is a successful measurement. Reserving
     non-zero for operational failure is what lets a caller read the token
     rather than `$?` — and `env` returning 0 on `PREFLIGHT: FAIL` is exactly
     why `alive codex && alive agy` is forbidden.
  3. **The docs table is pinned bidirectionally.** Every detail line the script
     can print must appear in SKILL.md and vice versa, or the two drift and the
     remedy table starts describing a gate that no longer exists.

So this emits those three by construction, plus the tests that PIN them and a
mutation spec that proves the pins bite. A scaffold that only emitted argparse
would save the cheap half.

    SCAFFOLD: WROTE name=<slug> token=<TOKEN> files=3
    SCAFFOLD: REFUSED reason=<reason>

exit 0 on a write, 2 on a refusal. Stdlib-only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TOKEN = "SCAFFOLD"
SLUG = re.compile(r"^[a-z][a-z0-9_]*$")
TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9-]*$")


class Refusal(Exception):
    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


def existing_tokens(skill_md: Path) -> set[str]:
    """Verdict tokens already documented in SKILL.md's helper registry."""
    try:
        text = skill_md.read_text()
    except OSError:
        return set()
    return set(re.findall(r"`?\b([A-Z][A-Z0-9-]{2,})`?:\s*(?:[A-Z]+\|)*[A-Z]+", text))


SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
"""h_mad_{slug}.py — TODO: one line on what question this answers.

TODO: say what a FAIL means and what it does NOT mean. The most useful sentence
in every gate in this repo is the one distinguishing a real finding from a
cannot-judge.

    {token}: {verdicts_bar} {count_name}=N
    {token}: {cannot} reason=<reason>

exit 0 on a verdict, 2 on a cannot-judge. Read the token, never `$?`.

Note the shape of the cannot-judge line: it carries NO `{count_name}=`. A zero is
byte-identical to "nothing was measured", and the zero reads as clean.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOKEN = "{token}"


def check(target: Path) -> dict:
    """Compute the verdict. Returns a dict; raises nothing for a FAIL.

    A cannot-judge is `{{"verdict": "{cannot}", "reason": "..."}}` with NO
    count key at all — not a count of zero.
    """
    try:
        text = target.read_text()
    except OSError:
        return {{"verdict": "{cannot}", "reason": "unreadable"}}

    # TODO: the actual check. `details` are machine-readable lines, one per
    # finding, each of which MUST have a row in SKILL.md's remedy table.
    details: list[str] = []
    if not text:
        details.append("EMPTY: the target had no content")

    return {{
        "verdict": "{fail}" if details else "{ok}",
        "{count_name}": len(details),
        "details": details,
    }}


def render(result: dict) -> str:
    if "{count_name}" not in result:
        # Cannot-judge: no count, deliberately.
        return f"{{TOKEN}}: {{result['verdict']}} reason={{result['reason']}}"
    return f"{{TOKEN}}: {{result['verdict']}} {count_name}={{result['{count_name}']}}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", type=Path)
    args = ap.parse_args(argv)

    result = check(args.target)
    print(render(result))
    for detail in result.get("details", []):
        print(f"  {{detail}}")
    print(f"[H-MAD] {slug} {{result['verdict'].lower()}}")

    # Exit 0 on ANY verdict. A {fail} is a successful measurement; only a
    # cannot-judge is an operational failure.
    return 2 if result["verdict"] == "{cannot}" else 0


if __name__ == "__main__":
    sys.exit(main())
'''

TEST_TEMPLATE = '''"""Tests for `h_mad_{slug}.py`.

The first three classes are NOT about this gate's subject. They pin the three
invariants every verdict-token gate in this repo shares, each of which has been
got wrong at least once — a cannot-judge that carried a count and read as clean,
a FAIL that exited non-zero so callers branched on `$?`, and a remedy table that
drifted from the detail lines it documents.

Do not delete them when you fill in the subject-specific tests below.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS / "h_mad_{slug}.py"
sys.path.insert(0, str(SCRIPTS))

from h_mad_{slug} import TOKEN, check, render  # noqa: E402


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


class TestCannotJudgeCarriesNoCount:
    """A zero is byte-identical to "nothing was measured", and reads as clean."""

    def test_the_cannot_judge_line_has_no_count(self, tmp_path: Path) -> None:
        proc = run_cli(str(tmp_path / "absent"))
        assert "{token}: {cannot}" in proc.stdout
        assert "{count_name}=" not in proc.stdout, proc.stdout

    def test_render_omits_the_count_when_there_is_none(self) -> None:
        line = render({{"verdict": "{cannot}", "reason": "unreadable"}})
        assert "{count_name}=" not in line
        assert "reason=" in line

    def test_a_real_verdict_does_carry_its_count(self, tmp_path: Path) -> None:
        """The accept direction: a gate that never counts protects nothing."""
        target = tmp_path / "t.txt"
        target.write_text("content")
        assert "{count_name}=" in render(check(target))


class TestExitCodes:
    """Exit 0 on a verdict. A {fail} is a successful measurement."""

    def test_a_verdict_exits_zero(self, tmp_path: Path) -> None:
        target = tmp_path / "t.txt"
        target.write_text("content")
        assert run_cli(str(target)).returncode == 0

    def test_a_fail_still_exits_zero(self, tmp_path: Path) -> None:
        target = tmp_path / "t.txt"
        target.write_text("")
        proc = run_cli(str(target))
        assert "{token}: {fail}" in proc.stdout
        assert proc.returncode == 0, "a FAIL is a verdict, not an operational error"

    def test_only_a_cannot_judge_exits_non_zero(self, tmp_path: Path) -> None:
        assert run_cli(str(tmp_path / "absent")).returncode == 2


class TestDocsArePinnedBothWays:
    """Detail line in the script <=> row in SKILL.md's remedy table."""

    def test_the_token_is_registered(self) -> None:
        assert "h_mad_{slug}.py" in (SKILL_DIR / "SKILL.md").read_text()

    def test_every_detail_prefix_is_documented(self) -> None:
        script = SCRIPT.read_text()
        skill = (SKILL_DIR / "SKILL.md").read_text()
        prefixes = set(re.findall(r'"([A-Z][A-Z_]+):', script))
        undocumented = sorted(p for p in prefixes if p not in skill)
        assert not undocumented, f"detail lines with no remedy row: {{undocumented}}"

    def test_every_documented_prefix_still_exists(self) -> None:
        """The other direction: a remedy row for a line the gate cannot print."""
        script = SCRIPT.read_text()
        skill = (SKILL_DIR / "SKILL.md").read_text()
        entry = next((ln for ln in skill.split("\\n") if "h_mad_{slug}.py" in ln), "")
        documented = set(re.findall(r"`([A-Z][A-Z_]+):`", entry))
        stale = sorted(d for d in documented if f'"{{d}}:' not in script)
        assert not stale, f"remedy rows for detail lines that no longer exist: {{stale}}"


class TestTheSubject:
    """TODO: what this gate is actually for. Delete this docstring, not the
    classes above."""

    def test_todo(self) -> None:
        pytest.skip("TODO: write the subject-specific tests")
'''


def mutation_spec(slug: str, token: str, count_name: str, cannot: str, fail: str,
                  ok: str, skill_dir: Path) -> dict:
    script = f"scripts/h_mad_{slug}.py"
    test = f"tests/test_h_mad_{slug}.py::"
    return {
        "_why": (
            "The first three mutations are the shared gate invariants, not this gate's "
            "subject: a cannot-judge that carries a count reads as a clean zero, a FAIL "
            "that exits non-zero makes callers branch on `$?`, and a docs table that is "
            "not pinned both ways drifts from the lines it documents. Keep them when you "
            "add the subject-specific mutations."
        ),
        # The tree the spec runs against is the tree it was scaffolded INTO,
        # not wherever this generator happens to live.
        "root": str(skill_dir),
        "command": ["python3.11", "-m", "pytest", f"tests/test_h_mad_{slug}.py", "-q"],
        "target_command": ["python3.11", "-m", "pytest", "-q"],
        "mutations": [
            {
                "name": "cannot-judge-carries-a-count",
                "_mechanism": (
                    "A zero is byte-identical to 'nothing was measured' and reads as "
                    "clean. This is #39's exact shape."
                ),
                "file": script,
                "find": f'    if "{count_name}" not in result:',
                "replace": "    if False:",
                "test": test + "TestCannotJudgeCarriesNoCount::test_the_cannot_judge_line_has_no_count",
            },
            {
                "name": "a-fail-exits-non-zero",
                "_mechanism": (
                    "Makes a successful measurement look like an operational error, so "
                    "callers branch on `$?` and a FAIL reads as a crash."
                ),
                "file": script,
                "find": f'    return 2 if result["verdict"] == "{cannot}" else 0',
                # Keyed on the PASS word, not the FAIL word: replacing with
                # `0 if verdict == FAIL else 2` leaves a FAIL exiting 0, so the
                # mutant is EQUIVALENT for the very test it is pinned to and
                # reports as a survivor. Measured when this scaffold was built.
                "replace": f'    return 0 if result["verdict"] == "{ok}" else 2',
                "test": test + "TestExitCodes::test_a_fail_still_exits_zero",
            },
            {
                "name": "a-detail-line-with-no-remedy-row",
                "_mechanism": (
                    "A finding the operator is told about with nowhere to look it up. "
                    "The bidirectional pin is what stops the table drifting."
                ),
                "file": script,
                "find": '        details.append("EMPTY: the target had no content")',
                "replace": '        details.append("UNDOCUMENTED: no remedy row exists for this")',
                "test": test + "TestDocsArePinnedBothWays::test_every_detail_prefix_is_documented",
            },
        ],
    }


REGISTRY_LINE = (
    "- `h_mad_{slug}.py` — TODO one line: `check()` + CLI printing "
    "`{token}: {verdicts_bar} {count_name}=N`, exit 0 on a verdict / 2 on "
    "`{token}: {cannot} reason=…`, which carries **no `{count_name}=`** so a "
    "cannot-judge can never be read as a clean zero. Detail lines: `EMPTY:`. "
    "Stdlib-only."
)


def scaffold(*, slug: str, token: str, ok: str, fail: str, cannot: str,
             count_name: str, skill_dir: Path, force: bool) -> list[Path]:
    if not SLUG.match(slug):
        raise Refusal("bad_slug", f"{slug!r} must be lower_snake_case")
    if not TOKEN_RE.match(token):
        raise Refusal("bad_token", f"{token!r} must be UPPER-KEBAB")
    taken = existing_tokens(skill_dir / "SKILL.md")
    if token in taken:
        raise Refusal(
            "token_taken",
            f"{token} is already a verdict token — two gates sharing one token means "
            f"a caller cannot tell which answered",
        )

    subs = dict(slug=slug, token=token, ok=ok, fail=fail, cannot=cannot,
                count_name=count_name, verdicts_bar=f"{ok}|{fail}")
    targets = {
        skill_dir / "scripts" / f"h_mad_{slug}.py": SCRIPT_TEMPLATE.format(**subs),
        skill_dir / "tests" / f"test_h_mad_{slug}.py": TEST_TEMPLATE.format(**subs),
        skill_dir / "tests" / "mutation-specs" / f"{slug}.json":
            json.dumps(mutation_spec(slug, token, count_name, cannot, fail, ok, skill_dir),
                       indent=1, ensure_ascii=False) + "\n",
    }
    existing = [p for p in targets if p.exists()]
    if existing and not force:
        raise Refusal("would_overwrite", ", ".join(str(p) for p in existing))

    for path, content in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    (skill_dir / "scripts" / f"h_mad_{slug}.py").chmod(0o755)
    return list(targets)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scaffold a verdict-token gate")
    ap.add_argument("--name", required=True, help="lower_snake_case, without the h_mad_ prefix")
    ap.add_argument("--token", required=True, help="UPPER-KEBAB verdict token")
    ap.add_argument("--pass-word", default="PASS")
    ap.add_argument("--fail-word", default="FAIL")
    ap.add_argument("--cannot-judge", default="UNREADABLE",
                    help="the cannot-judge verdict; it will carry no count")
    ap.add_argument("--count", default="issues", help="name of the count field")
    ap.add_argument("--skill-dir", type=Path, default=SKILL_DIR)
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args(argv)

    try:
        written = scaffold(
            slug=args.name, token=args.token, ok=args.pass_word, fail=args.fail_word,
            cannot=args.cannot_judge, count_name=args.count,
            skill_dir=args.skill_dir, force=args.force,
        )
    except Refusal as exc:
        print(f"{TOKEN}: REFUSED reason={exc.reason}")
        if exc.detail:
            print(f"  {exc.detail}")
        return 2

    print(f"{TOKEN}: WROTE name={args.name} token={args.token} files={len(written)}")
    for path in written:
        print(f"  {path}")
    print("\nPaste into SKILL.md's helper registry, then fill in the TODOs:")
    print(REGISTRY_LINE.format(
        slug=args.name, token=args.token, count_name=args.count,
        cannot=args.cannot_judge, verdicts_bar=f"{args.pass_word}|{args.fail_word}"))
    print(f"\n[H-MAD] {args.name} scaffold wrote")
    return 0


if __name__ == "__main__":
    sys.exit(main())
