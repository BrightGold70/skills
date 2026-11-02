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
import shutil
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
    # The generated pins read the registry through the skill's own corpus
    # reader, which every real h-mad skill dir ships beside its gates.
    if (SCRIPTS / "h_mad_skill_corpus.py").is_file():
        shutil.copy2(SCRIPTS / "h_mad_skill_corpus.py", tmp_path / "scripts")
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
        before = sorted(root.rglob("*"))
        proc = run_cli("--name", "Bad-Name", "--token", "X", "--skill-dir", str(root))
        assert proc.returncode == 2
        assert "SCAFFOLD: REFUSED" in proc.stdout
        assert sorted(root.rglob("*")) == before


class TestTokenDetection:
    def test_it_finds_the_tokens_already_in_the_real_registry(self) -> None:
        """Guards the collision check itself: a detector finding nothing would
        make every `token_taken` refusal unreachable."""
        found = existing_tokens(SKILL_DIR / "SKILL.md")
        for token in ("GATE", "WIREPIN", "MUTATION", "PRECONDITION"):
            assert token in found, f"{token} missing from {sorted(found)[:20]}"

    def test_an_unreadable_registry_is_refused_not_read_as_empty(
        self, tmp_path: Path
    ) -> None:
        """An empty set is byte-identical to "no token is taken", so reading a
        registry that could not be read as empty lets any token through."""
        with pytest.raises(Refusal) as exc:
            existing_tokens(tmp_path / "SKILL.md")
        assert exc.value.reason == "registry_unreadable"

    def test_a_broken_split_is_refused_not_read_as_empty(self, tmp_path: Path) -> None:
        root = split_skill_dir(tmp_path, "")
        # A reference that lost its split-body marker: skill_text raises
        # ValueError, not OSError (a deleted reference is FileNotFoundError).
        (root / "references" / SPLIT_REF).write_text("# no marker\n", encoding="utf-8")
        with pytest.raises(Refusal) as exc:
            existing_tokens(root / "SKILL.md")
        assert exc.value.reason == "registry_unreadable"

    def test_an_unreadable_registry_refuses_the_scaffold_and_writes_nothing(
        self, tmp_path: Path
    ) -> None:
        root = fake_skill_dir(tmp_path)
        (root / "SKILL.md").unlink()
        proc = run_cli("--name", "demo_gate", "--token", "DEMOGATE", "--skill-dir", str(root))
        assert proc.returncode == 2
        assert "SCAFFOLD: REFUSED reason=registry_unreadable" in proc.stdout
        assert not (root / "scripts" / "h_mad_demo_gate.py").exists()


SPLIT_REF = "phase5-substeps.md"
SPLIT_HEADING = "Phase 5 sub-steps"


def split_skill_dir(tmp_path: Path, moved_body: str) -> Path:
    """A skill dir whose registry text lives in a split reference, the shape
    rows 2910/2930 give the real SKILL.md: a stub in SKILL.md, the verbatim
    body behind a split-body marker in `references/`."""
    root = fake_skill_dir(tmp_path)
    (root / "SKILL.md").write_text(
        f"# fake skill\n\n## {SPLIT_HEADING}\n\nMoved to `references/{SPLIT_REF}`.\n\n"
        "## Last\n\nend\n", encoding="utf-8")
    (root / "references").mkdir()
    (root / "references" / SPLIT_REF).write_text(
        f"# {SPLIT_HEADING}\n\n<!-- h-mad split body: SKILL.md §\"{SPLIT_HEADING}\" -->\n"
        + moved_body, encoding="utf-8")
    return root


class TestTheRegistryIsReadWithItsSplitSectionsRestored:
    """Rows 2910/2930 move SKILL.md sections into `references/`. The registry
    the collision check and the generated pins read is the restored text, or a
    token documented only in a moved section is silently free again."""

    def test_a_token_documented_only_in_a_split_reference_is_refused(
        self, tmp_path: Path
    ) -> None:
        root = split_skill_dir(
            tmp_path, "- `h_mad_other.py` — CLI printing `DEMOGATE: PASS|FAIL issues=N`\n\n")
        assert "DEMOGATE" not in (root / "SKILL.md").read_text(), (
            "control: the token must be absent from the raw SKILL.md")
        with pytest.raises(Refusal) as exc:
            make(tmp_path, root=root)
        assert exc.value.reason == "token_taken"

    def test_the_real_registry_reads_as_the_restored_skill_text(self) -> None:
        from h_mad_skill_corpus import skill_text
        restored = skill_text(SKILL_DIR)
        assert existing_tokens(SKILL_DIR / "SKILL.md") == existing_tokens_in(restored)

    def test_the_generated_pins_read_a_registry_line_in_a_split_reference(
        self, tmp_path: Path
    ) -> None:
        root = split_skill_dir(tmp_path, "")
        proc = run_cli("--name", "demo_gate", "--token", "DEMOGATE", "--skill-dir", str(root))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        line = next(ln for ln in proc.stdout.split("\n") if ln.startswith("- `h_mad_"))
        with (root / "references" / SPLIT_REF).open("a", encoding="utf-8") as fh:
            fh.write(line + "\n\n")
        assert "h_mad_demo_gate.py" not in (root / "SKILL.md").read_text()
        suite = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_h_mad_demo_gate.py", "-q",
             "-k", "Docs"], cwd=str(root), capture_output=True, text=True)
        assert suite.returncode == 0, suite.stdout + suite.stderr
        assert "3 passed" in suite.stdout, suite.stdout


def existing_tokens_in(text: str) -> set[str]:
    import re
    return set(re.findall(r"`?\b([A-Z][A-Z0-9-]{2,})`?:\s*(?:[A-Z]+\|)*[A-Z]+", text))
