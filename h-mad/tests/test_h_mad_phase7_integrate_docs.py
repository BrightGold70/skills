"""Every blocker 7f can emit must be named in SKILL.md (#18).

#18 was filed as "7f unrunnable when the base exists only as a remote-tracking
ref". Re-probed on a clone whose `main` existed only as `origin/main`, that
premise is FALSE and the script is right:

    --base origin/main   -> BLOCKED reason=base_not_a_local_branch:origin/main
    (no --base)          -> BLOCKED reason=no_default_base

Both are correct refusals. You cannot merge into a remote-tracking ref —
`git checkout origin/main` DETACHES, and `local_branch_exists`'s docstring
records a measured run where that produced `MERGED` at exit 0 with the merge
commit unreferenced and the base never moved. The remedy is to create the local
branch, and choosing where it starts is not 7f's judgement to make.

What IS defective is the documentation, and precisely in this scenario: SKILL.md
listed five of the ten blockers, and BOTH tokens an operator hits here were among
the five it omitted. An operator reads a token that appears nowhere in the skill
and has no way to learn that `--base` must be a local branch. It also documented
`nothing_to_integrate:<branch>` while the emitted token is
`nothing_to_integrate:<branch>_is_not_ahead_of_<base>`.

A prose list nothing checks drifts the moment a blocker is added — the defect
here is exactly that drift, so the list is enforced rather than restated.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_phase7_integrate.py"
SKILL_MD = REPO_ROOT / "h-mad" / "SKILL.md"


def emitted_blockers() -> set[str]:
    """The STABLE prefix of every `blockers.append(...)` literal in the script.

    Matched across a newline because several appends wrap. The prefix is
    everything before the first interpolation, which is what SKILL.md can name
    without restating a runtime value.
    """
    text = SCRIPT.read_text()
    found = set()
    for m in re.finditer(r'blockers\.append\(\s*\n?\s*f?"([^"]+)"', text):
        found.add(m.group(1).split("{", 1)[0].rstrip(":"))
    assert found, "no blockers found — the extraction broke, which is not an empty set"
    return found


def integrate_paragraph() -> str:
    """The 7f paragraph, addressed by the script it documents rather than by a
    line number that every edit above it moves."""
    for line in SKILL_MD.read_text().splitlines():
        if "h_mad_phase7_integrate.py" in line and "BLOCKED" in line:
            return line
    raise AssertionError("the 7f paragraph naming h_mad_phase7_integrate.py is gone")


def test_every_blocker_the_script_emits_is_documented() -> None:
    para = integrate_paragraph()
    missing = sorted(b for b in emitted_blockers() if f"`{b}" not in para)
    assert not missing, (
        f"7f can emit these and SKILL.md does not name them: {missing}. "
        "An operator reads the token and finds nothing."
    )


def test_the_documented_nothing_to_integrate_token_matches_the_emitted_one() -> None:
    """A documented token an operator cannot match against real output is worse
    than an undocumented one — it reads as a different blocker."""
    assert "nothing_to_integrate:{branch}_is_not_ahead_of_{base}" in SCRIPT.read_text()
    assert "nothing_to_integrate:<branch>_is_not_ahead_of_<base>" in integrate_paragraph()


def test_the_local_branch_requirement_on_base_is_stated() -> None:
    """The whole of #18. Without this an operator whose trunk is remote-only has
    no documented route forward."""
    para = integrate_paragraph()
    assert "must name a LOCAL branch" in para
    assert "git branch main origin/main" in para, "the remedy is named, not just the rule"
