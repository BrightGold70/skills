"""Tests for `h_mad_new_gate.py`.

A scaffold that emits boilerplate is worth little; the reason this one exists is
that it emits three INVARIANTS by construction, each of which has been got wrong
in this repo at least once. So the load-bearing test here is not "it wrote three
files" — it is `TestTheScaffoldedGateIsSound`, which runs the generated suite AND
the generated mutation spec against the generated gate. If the emitted pins do
not bite, the scaffold is worse than nothing: it ships the appearance of
coverage.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS / "h_mad_new_gate.py"
HARNESS = SCRIPTS / "h_mad_mutation_harness.py"
sys.path.insert(0, str(SCRIPTS))

from h_mad_new_gate import Refusal, existing_tokens, scaffold  # noqa: E402


def fake_skill_dir(tmp_path: Path) -> Path:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests" / "mutation-specs").mkdir(parents=True)
    (tmp_path / "SKILL.md").write_text("# fake skill\n", encoding="utf-8")
    return tmp_path


def make(tmp_path: Path, **kw) -> Path:
    root = kw.pop("root", None) or fake_skill_dir(tmp_path)
    args = dict(slug="demo_gate", token="DEMOGATE", ok="PASS", fail="FAIL",
                cannot="UNREADABLE", count_name="issues", skill_dir=root, force=False)
    args.update(kw)
    scaffold(**args)
    return root


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def paste_registry_line(root: Path, proc_stdout: str) -> None:
    line = next(ln for ln in proc_stdout.split("\n") if ln.startswith("- `h_mad_"))
    with (root / "SKILL.md").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


class TestTheScaffoldedGateIsSound:
    """The whole point. A scaffold whose pins do not bite ships fake coverage."""

    def test_a_scaffolded_gate_passes_its_own_suite(self, tmp_path: Path) -> None:
        root = fake_skill_dir(tmp_path)
        proc = run_cli("--name", "demo_gate", "--token", "DEMOGATE",
                       "--skill-dir", str(root))
        assert proc.returncode == 0, proc.stdout
        paste_registry_line(root, proc.stdout)

        suite = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q"],
            cwd=str(root), capture_output=True, text=True)
        assert suite.returncode == 0, suite.stdout + suite.stderr

    def test_the_scaffolded_gates_own_mutations_all_bite(self, tmp_path: Path) -> None:
        """Runs the emitted mutation spec against the emitted gate.

        One emitted mutation initially SURVIVED: replacing the exit line with
        `0 if verdict == FAIL else 2` leaves a FAIL exiting 0, so it was
        equivalent for the very test it was pinned to. A scaffold that ships a
        mutation which cannot fail is teaching the wrong lesson at scale.
        """
        root = fake_skill_dir(tmp_path)
        proc = run_cli("--name", "demo_gate", "--token", "DEMOGATE",
                       "--skill-dir", str(root))
        paste_registry_line(root, proc.stdout)

        spec = root / "tests" / "mutation-specs" / "demo_gate.json"
        run = subprocess.run(
            [sys.executable, str(HARNESS), str(spec)],
            cwd=str(root), capture_output=True, text=True)
        assert "MUTATION: ALL_CAUGHT" in run.stdout, run.stdout

    def test_the_emitted_spec_targets_the_tree_it_was_scaffolded_into(
        self, tmp_path: Path
    ) -> None:
        """It used the generator's own SKILL_DIR, so every emitted spec pointed
        at the real h-mad tree regardless of `--skill-dir`."""
        root = make(tmp_path)
        spec = json.loads((root / "tests" / "mutation-specs" / "demo_gate.json").read_text())
        assert spec["root"] == str(root)
        assert str(SKILL_DIR) != spec["root"]


class TestTheThreeInvariantsAreEmitted:
    def test_the_cannot_judge_line_carries_no_count(self, tmp_path: Path) -> None:
        root = make(tmp_path)
        gate = (root / "scripts" / "h_mad_demo_gate.py").read_text()
        assert 'if "issues" not in result:' in gate
        assert "reason={result['reason']}" in gate

    def test_a_verdict_exits_zero(self, tmp_path: Path) -> None:
        root = make(tmp_path)
        gate = (root / "scripts" / "h_mad_demo_gate.py").read_text()
        assert 'return 2 if result["verdict"] == "UNREADABLE" else 0' in gate

    def test_the_docs_pin_runs_both_ways(self, tmp_path: Path) -> None:
        root = make(tmp_path)
        tests = (root / "tests" / "test_h_mad_demo_gate.py").read_text()
        # Anchored on the `def` so a method renamed out of collection (a
        # leading underscore) fails: the bare substring survives that rename,
        # which is how the mutation for this pin first survived.
        assert "def test_every_detail_prefix_is_documented" in tests
        assert "def test_every_documented_prefix_still_exists" in tests

    def test_the_docs_pin_is_red_until_the_registry_line_is_pasted(
        self, tmp_path: Path
    ) -> None:
        """Deliberate: the doc step is the one most easily skipped, so the
        generated suite fails until it is done."""
        root = fake_skill_dir(tmp_path)
        run_cli("--name", "demo_gate", "--token", "DEMOGATE", "--skill-dir", str(root))
        suite = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q"],
            cwd=str(root), capture_output=True, text=True)
        assert suite.returncode != 0
        assert "test_the_token_is_registered" in suite.stdout


class TestRefusals:
    def test_a_token_already_in_use_is_refused(self, tmp_path: Path) -> None:
        """Two gates sharing one token means a caller cannot tell which answered."""
        root = fake_skill_dir(tmp_path)
        (root / "SKILL.md").write_text(
            "- `h_mad_other.py` — CLI printing `DEMOGATE: PASS|FAIL issues=N`\n",
            encoding="utf-8")
        with pytest.raises(Refusal) as exc:
            make(tmp_path, root=root)
        assert exc.value.reason == "token_taken"

    @pytest.mark.parametrize("slug", ["Demo", "demo-gate", "2demo", ""])
    def test_a_bad_slug_is_refused(self, tmp_path: Path, slug: str) -> None:
        with pytest.raises(Refusal) as exc:
            make(tmp_path, slug=slug)
        assert exc.value.reason == "bad_slug"

    @pytest.mark.parametrize("token", ["demogate", "Demo_Gate", "1GATE"])
    def test_a_bad_token_is_refused(self, tmp_path: Path, token: str) -> None:
        with pytest.raises(Refusal) as exc:
            make(tmp_path, token=token)
        assert exc.value.reason == "bad_token"

    def test_it_will_not_overwrite_without_force(self, tmp_path: Path) -> None:
        root = make(tmp_path)
        with pytest.raises(Refusal) as exc:
            make(tmp_path, root=root, token="OTHERGATE")
        assert exc.value.reason == "would_overwrite"

    def test_force_overwrites(self, tmp_path: Path) -> None:
        root = make(tmp_path)
        make(tmp_path, root=root, token="OTHERGATE", force=True)
        assert "OTHERGATE" in (root / "scripts" / "h_mad_demo_gate.py").read_text()

    def test_a_refusal_exits_two_and_writes_nothing(self, tmp_path: Path) -> None:
        root = fake_skill_dir(tmp_path)
        proc = run_cli("--name", "Bad-Name", "--token", "X", "--skill-dir", str(root))
        assert proc.returncode == 2
        assert "SCAFFOLD: REFUSED" in proc.stdout
        assert not list((root / "scripts").iterdir())


class TestTokenDetection:
    def test_it_finds_the_tokens_already_in_the_real_registry(self) -> None:
        """Guards the collision check itself: a detector finding nothing would
        make every `token_taken` refusal unreachable."""
        found = existing_tokens(SKILL_DIR / "SKILL.md")
        for token in ("GATE", "WIREPIN", "MUTATION", "PRECONDITION"):
            assert token in found, f"{token} missing from {sorted(found)[:20]}"

    def test_an_unreadable_registry_yields_no_tokens_rather_than_raising(
        self, tmp_path: Path
    ) -> None:
        assert existing_tokens(tmp_path / "absent.md") == set()
