"""H5 — a shared sentence is single-sourced, and adoption is checked BEFORE commit.

The failure this closes is invisible to every audit leg by construction. Measured:
two authors independently corrected one shared fact in the same cycle, one to **18**
and one to **20**. Each document was internally consistent, so a reviewer reading any
single document found nothing, and a reviewer reading both had no reason to diff one
sentence out of thousands. Three of the last five cycles' must-fixes on `#18
gateway-consolidation` were propagation gaps of this shape.

Today the cross-document reading is `doc-auditor` rule 7 — a reviewer pass that runs
in the NEXT cycle, after the divergence is already committed. H5 moves it before the
commit and makes it mechanical: the design decides one sentence, the siblings quote it
verbatim, and this check says which ones did not.

**Whitespace is normalised and that is the whole difficulty.** Documents hard-wrap at
different columns, so the same sentence is a different byte string in each file — this
repo has a measured case of a hard wrap hiding a retired count from every single-line
grep for 92 cycles. A checker that compared raw bytes would report DIVERGED on
documents that had adopted the sentence perfectly, which is the calibration error that
gets a gate switched off.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "h-mad" / "scripts"
SCRIPT = SCRIPTS / "h_mad_adoption_check.py"
sys.path.insert(0, str(SCRIPTS))

SENTENCE = "The registry holds 18 trial families."


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def token(out: str, prefix: str = "ADOPTION:") -> str:
    for line in out.splitlines():
        if line.startswith(prefix):
            return line
    return ""


def _doc(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


class TestAdoption:
    def test_every_sibling_quoting_the_sentence_is_ADOPTED(self, tmp_path: Path) -> None:
        a = _doc(tmp_path, "a.md", f"intro\n\n{SENTENCE}\n\nmore\n")
        b = _doc(tmp_path, "b.md", f"other\n\n{SENTENCE}\n")
        out = run("--sentence", SENTENCE, "--doc", str(a), "--doc", str(b))
        assert out.returncode == 0, out.stdout + out.stderr
        assert token(out.stdout).startswith("ADOPTION: ADOPTED docs=2")

    def test_a_sibling_that_did_not_adopt_is_DIVERGED_and_named(self, tmp_path: Path) -> None:
        """THE defect: one document says 18, its sibling says 20, both consistent."""
        a = _doc(tmp_path, "a.md", f"{SENTENCE}\n")
        b = _doc(tmp_path, "b.md", "The registry holds 20 trial families.\n")
        out = run("--sentence", SENTENCE, "--doc", str(a), "--doc", str(b))
        line = token(out.stdout)
        assert "DIVERGED" in line
        assert "b.md" in out.stdout
        assert "a.md" not in line, "the adopting sibling must not be named as missing"

    def test_a_hard_wrap_is_still_adoption(self, tmp_path: Path) -> None:
        """The load-bearing case. A byte comparison reports DIVERGED here and is wrong.

        Measured in this repo: a hard wrap hid a retired count from every single-line
        grep for 92 cycles.
        """
        a = _doc(tmp_path, "a.md", f"{SENTENCE}\n")
        b = _doc(tmp_path, "b.md", "The registry holds 18\ntrial families.\n")
        out = run("--sentence", SENTENCE, "--doc", str(a), "--doc", str(b))
        assert "ADOPTED" in token(out.stdout), out.stdout

    def test_leading_indentation_and_bullets_do_not_break_adoption(self, tmp_path: Path) -> None:
        a = _doc(tmp_path, "a.md", f"{SENTENCE}\n")
        b = _doc(tmp_path, "b.md", f"  -   {SENTENCE}\n")
        assert "ADOPTED" in token(run("--sentence", SENTENCE,
                                      "--doc", str(a), "--doc", str(b)).stdout)

    def test_an_unreadable_document_is_UNREADABLE_never_DIVERGED(self, tmp_path: Path) -> None:
        """Fail closed. "I could not read it" and "it did not adopt" have opposite fixes."""
        a = _doc(tmp_path, "a.md", f"{SENTENCE}\n")
        missing = tmp_path / "gone.md"
        out = run("--sentence", SENTENCE, "--doc", str(a), "--doc", str(missing))
        assert out.returncode == 2
        assert "UNREADABLE" in token(out.stdout)
        assert "DIVERGED" not in out.stdout

    def test_one_document_is_not_an_adoption_check(self, tmp_path: Path) -> None:
        """Adoption is a relation between siblings; a single doc cannot exhibit it."""
        a = _doc(tmp_path, "a.md", f"{SENTENCE}\n")
        out = run("--sentence", SENTENCE, "--doc", str(a))
        assert "UNREADABLE" in token(out.stdout) or "not_two_docs" in out.stdout

    def test_an_empty_sentence_is_refused_not_trivially_adopted(self, tmp_path: Path) -> None:
        """`"" in text` is True for every document — a vacuous ADOPTED on every input."""
        a = _doc(tmp_path, "a.md", "anything\n")
        b = _doc(tmp_path, "b.md", "anything\n")
        out = run("--sentence", "   ", "--doc", str(a), "--doc", str(b))
        assert out.returncode == 2
        assert "ADOPTED" not in out.stdout

    def test_the_sentence_can_come_from_a_file(self, tmp_path: Path) -> None:
        """The canonical sentence lives in the design; retyping it is how it drifts."""
        src = _doc(tmp_path, "src.txt", SENTENCE + "\n")
        a = _doc(tmp_path, "a.md", f"{SENTENCE}\n")
        b = _doc(tmp_path, "b.md", f"x {SENTENCE} y\n")
        out = run("--sentence-file", str(src), "--doc", str(a), "--doc", str(b))
        assert "ADOPTED" in token(out.stdout), out.stdout

    def test_the_verdict_is_a_token_not_an_exit_code(self, tmp_path: Path) -> None:
        """Every h-mad gate is read by token; DIVERGED is a verdict, exit 0."""
        a = _doc(tmp_path, "a.md", f"{SENTENCE}\n")
        b = _doc(tmp_path, "b.md", "nothing here\n")
        out = run("--sentence", SENTENCE, "--doc", str(a), "--doc", str(b))
        assert out.returncode == 0
        assert token(out.stdout).startswith("ADOPTION: DIVERGED")
