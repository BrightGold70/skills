"""The h-mad skill body as its readers should read it: SKILL.md with its split sections restored.

Row 2910 moved three large SKILL.md sections into `h-mad/references/` so that the
body loaded on every `/h-mad` invocation shrinks. In SKILL.md each one is now a
short pointer stub under its original `## ` heading. The reference file carries a
marker line, and everything below it is the section body exactly as it stood.

`skill_text()` puts each body back in place of its stub, so it returns the text
SKILL.md held before the split, byte for byte. That is deliberate. Pins that
slice a section by heading (`docsections.titled_section`), compare positions,
count occurrences or assert `"X" not in text` all keep measuring what they
measured before. Concatenating the references at the end would have silently
changed every one of those.

What this reconstruction does NOT read is the stub's own wording. Pins on the
stubs belong in `test_h_mad_skill_budget.py`, which reads SKILL.md directly.

Failure is loud, in both directions. A stub that links a split reference which
is missing, has no marker, or names a different heading raises; so does a split
reference that exists but is no longer linked, and a file under `references/`
carrying the marker that `SPLIT_REFERENCES` does not list. A pin must never pass because the
text it guards silently stopped being read.

Before the split lands, SKILL.md links no split reference and `skill_text()`
is SKILL.md unchanged.

It lives in `scripts/` because production reads it too: `h_mad_new_gate.py`'s
token-collision check and the pins it generates read the helper registry, which
row 2930 moves out of SKILL.md. `tests/skill_corpus.py` re-exports it for the
tests. Stdlib-only.
"""
from __future__ import annotations

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]

SPLIT_REFERENCES = (
    "references/phase5-substeps.md",
    "references/teammate-authors.md",
    "references/audit-prompt-assembly.md",
    "references/helper-scripts.md",
)

_MARKER = re.compile(r'^<!-- h-mad split body: SKILL\.md §"(?P<heading>[^"\n]+)" -->\n', re.M)


def _split_body(path: Path) -> tuple[str, str]:
    """(heading, verbatim body) from a split reference file."""
    if not path.is_file():
        raise FileNotFoundError(
            f"SKILL.md links {path.name} but {path} does not exist; "
            "the pins on its text would silently stop reading it"
        )
    text = path.read_text(encoding="utf-8")
    markers = list(_MARKER.finditer(text))
    if len(markers) != 1:
        raise ValueError(f"{path} must carry exactly one split-body marker, found {len(markers)}")
    m = markers[0]
    return m.group("heading"), text[m.end():]


def doc_text(path: Path, encoding: str = "utf-8") -> str:
    """`path.read_text()`, except a `SKILL.md` reads as `skill_text()` of its directory.

    Lets a helper that is handed many documents (`(SKILL, "SKILL.md"), (BASE, …)`)
    switch with one call site and leave every other document's read unchanged.
    """
    path = Path(path)
    if path.name == "SKILL.md":
        return skill_text(path.parent)
    return path.read_text(encoding=encoding)


def skill_text(skill_dir: Path = SKILL_DIR) -> str:
    """SKILL.md with every split section's body restored in place of its stub."""
    skill_dir = Path(skill_dir)
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    unlisted = sorted(
        f"references/{p.name}" for p in (skill_dir / "references").glob("*.md")
        if f"references/{p.name}" not in SPLIT_REFERENCES
        and _MARKER.search(p.read_text(encoding="utf-8", errors="replace"))
    ) if (skill_dir / "references").is_dir() else []
    if unlisted:
        raise ValueError(f"split-body marker in {unlisted}, which SPLIT_REFERENCES does not "
                         "list: add it there, or nothing restores or checks it")
    for rel in SPLIT_REFERENCES:
        linked, exists = rel in text, (skill_dir / rel).is_file()
        if not linked and not exists:
            continue  # this section was never split
        if exists and not linked:
            raise ValueError(f"{rel} exists but SKILL.md no longer links it: its stub lost "
                             "the pointer, and its text would silently stop being read")
        heading, body = _split_body(skill_dir / rel)
        head_line = f"## {heading}\n"
        starts = [m.start() for m in re.finditer(re.escape(head_line), text)
                  if m.start() == 0 or text[m.start() - 1] == "\n"]
        if len(starts) != 1:
            raise ValueError(f"SKILL.md must hold the stub heading {head_line.strip()!r} "
                             f"exactly once, found {len(starts)}")
        body_start = starts[0] + len(head_line)
        nxt = re.compile(r"^## ", re.M).search(text, body_start)
        if nxt is None:
            raise ValueError(f"stub {head_line.strip()!r} is not followed by another ## heading")
        stub = text[body_start:nxt.start()]
        if rel not in stub:
            raise ValueError(f"{rel} is linked from SKILL.md but not from the "
                             f"{head_line.strip()!r} stub that owns it")
        text = text[:body_start] + body + text[nxt.start():]
    return text
