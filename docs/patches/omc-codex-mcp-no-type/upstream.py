#!/usr/bin/env python3
"""Check whether OMC's newest release tag still writes `type` into Codex MCP blocks.

Run it BEFORE updating OMC. It reads the two compiled runtime files at the tag
(dist/installer/mcp-registry.js, bridge/cli.cjs) from GitHub, never the source .ts:
5.8.3 shipped a fixed .ts with a stale build.

Exit 0  UPSTREAM: FIXED      neither file emits `type` and both still carry the
                             renderer; the patch can be retired (README §Retiring).
Exit 1  UPSTREAM: EMITS      the exact emission line is still there; after the
                             update, re-apply with apply.py.
Exit 2  UPSTREAM: UNREADABLE could not judge: gh failed, a file is missing or empty,
                             the renderer is gone, or a `type = ${...}` emission is
                             spelled differently from the line apply.py knows.
                             That is not "fixed". Read the files by hand.

  --tag TAG       check this tag instead of the newest release
  --from-dir DIR  read the two files from DIR (flat: mcp-registry.js, cli.cjs)
                  instead of GitHub; used by the tests, needs no network
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from targets import ORIGINAL, RELATIVE  # noqa: E402

REPO = "Yeachan-Heo/oh-my-claudecode"
RENDERER = "renderCodexServerBlock"
# Any `type = ${...}` template. In the v5.8.4 build it matches only the emission
# line, so a hit the exact ORIGINAL pattern misses means upstream respelled it.
LOOSE = re.compile(r"type\s*=\s*\$\{")


def gh(*args: str) -> str:
    out = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)}: {out.stderr.strip() or out.returncode}")
    return out.stdout


def newest_tag() -> str:
    tag = gh("release", "view", "-R", REPO, "--json", "tagName", "-q", ".tagName").strip()
    if not tag:
        raise RuntimeError("gh release view returned no tagName")
    return tag


def fetch(tag: str, rel: str) -> str:
    return gh("api", "-H", "Accept: application/vnd.github.raw",
              f"repos/{REPO}/contents/{rel}?ref={tag}")


def judge(name: str, text: str) -> tuple[str, str]:
    """Return (verdict, detail) for one file: FIXED, EMITS or UNREADABLE."""
    if not text.strip():
        return "UNREADABLE", f"{name} is empty"
    if RENDERER not in text:
        return "UNREADABLE", f"{name} no longer contains {RENDERER}"
    exact = len(ORIGINAL.findall(text))
    loose = len(LOOSE.findall(text))
    if exact:
        return "EMITS", f"{name} emission line x{exact}"
    if loose:
        return "UNREADABLE", f"{name} has {loose} `type = ${{` template(s) the exact pattern does not match"
    return "FIXED", f"{name} no emission"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check OMC's newest release tag for the Codex `type` emission.")
    ap.add_argument("--tag")
    ap.add_argument("--from-dir", type=Path)
    a = ap.parse_args(argv)

    try:
        tag = a.tag or ("local" if a.from_dir else newest_tag())
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"UPSTREAM: UNREADABLE cannot resolve the newest tag ({exc})")
        return 2

    results = []
    for rel in RELATIVE:
        name = Path(rel).name
        try:
            text = (a.from_dir / name).read_text(encoding="utf-8") if a.from_dir else fetch(tag, rel)
        except (OSError, RuntimeError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
            results.append(("UNREADABLE", f"{name} unreadable ({exc})"))
            continue
        results.append(judge(name, text))

    verdicts = {v for v, _ in results}
    detail = "; ".join(d for _, d in results)
    # EMITS outranks UNREADABLE: one file proven to emit is already a definite answer.
    if "EMITS" in verdicts:
        print(f"UPSTREAM: EMITS {tag} — {detail}")
        return 1
    if "UNREADABLE" in verdicts:
        print(f"UPSTREAM: UNREADABLE {tag} — {detail}")
        return 2
    print(f"UPSTREAM: FIXED {tag} — {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
