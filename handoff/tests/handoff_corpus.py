"""The handoff skill body as tests should read it: SKILL.md with its split sections restored.

The handoff split (row 2930's second half) moved the READ, HANDOVER and
TAKEOVER mode bodies into `handoff/references/`, so a WRITE invocation no
longer loads ~74 KB it never runs. In SKILL.md each is a pointer stub under
its original `## ` heading; the reference carries a marker line and, below it,
the section body exactly as it stood.

`skill_text()` puts each body back in place of its stub, byte for byte, so
every pin that slices, counts or orders SKILL.md text keeps measuring what it
measured before. A missing, unmarked, unlinked or unlisted split reference
raises: a pin must never pass because its text silently stopped being read.

This mirrors `h-mad/scripts/h_mad_skill_corpus.py` deliberately rather than
importing it: the handoff skill is installed and used without h-mad, so its
tests must not depend on h-mad's tree. Keep the two in step.
"""
from __future__ import annotations

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]

SPLIT_REFERENCES = (
    "references/read-mode.md",
    "references/handover-mode.md",
    "references/takeover-mode.md",
)

_MARKER = re.compile(r'^<!-- handoff split body: SKILL\.md §"(?P<heading>[^"\n]+)" -->\n', re.M)


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
