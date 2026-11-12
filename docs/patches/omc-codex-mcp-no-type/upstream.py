#!/usr/bin/env python3
"""Check whether OMC's newest release still writes `type` into Codex MCP blocks.

Run it BEFORE updating OMC. It reads the two compiled runtime files
(dist/installer/mcp-registry.js, bridge/cli.cjs), never the source .ts (5.8.3
shipped a fixed .ts with a stale build), from both places an update comes from:

  tag  the GitHub release tag, via `gh api` (feeds the plugin cache)
  npm  the `oh-my-claude-sisyphus` tarball, via `npm pack` (feeds the global `omc`)

The npm version is the tag without its leading `v`; with no --tag, npm's own
`latest` is checked, and a mismatch with the newest tag is printed as a note.
Tarball members are read in memory; nothing is extracted to disk.

Exit 0  UPSTREAM: FIXED      no file in either source emits `type`, and every
                             file still carries the renderer; the patch can be
                             retired (README §Retiring).
Exit 1  UPSTREAM: EMITS      the exact emission line is still in at least one
                             file; after the update, re-apply with apply.py.
Exit 2  UPSTREAM: UNREADABLE could not judge: gh/npm failed, a file is missing or
                             empty, the renderer is gone, or a `type = ${...}`
                             emission is spelled differently from the line
                             apply.py knows. That is not "fixed". Read by hand.

  --tag TAG           check this tag (and npm version TAG without `v`)
  --from-dir DIR      offline: read the tag's two files from DIR (flat:
                      mcp-registry.js, cli.cjs)
  --npm-from-tgz FILE offline: read the npm files from this tarball
Offline inputs are for tests. When either is given, only the given sources are
checked and nothing touches the network.
"""
import argparse
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from targets import ORIGINAL, RELATIVE  # noqa: E402

REPO = "Yeachan-Heo/oh-my-claudecode"
NPM_PACKAGE = "oh-my-claude-sisyphus"
RENDERER = "renderCodexServerBlock"
# Any `type = ${...}` template. In the v5.8.4 build it matches only the emission
# line, so a hit the exact ORIGINAL pattern misses means upstream respelled it.
LOOSE = re.compile(r"type\s*=\s*\$\{")
TOOL_ERRORS = (OSError, RuntimeError, subprocess.SubprocessError, UnicodeDecodeError,
               tarfile.TarError)


def tool(*args: str, cwd: str | None = None) -> str:
    out = subprocess.run(list(args), capture_output=True, text=True, timeout=120, cwd=cwd)
    if out.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}: {out.stderr.strip() or out.returncode}")
    return out.stdout


def newest_tag() -> str:
    tag = tool("gh", "release", "view", "-R", REPO, "--json", "tagName", "-q", ".tagName").strip()
    if not tag:
        raise RuntimeError("gh release view returned no tagName")
    return tag


def npm_latest() -> str:
    ver = tool("npm", "view", NPM_PACKAGE, "version").strip()
    if not ver:
        raise RuntimeError("npm view returned no version")
    return ver


def fetch_tag(tag: str, rel: str) -> str:
    return tool("gh", "api", "-H", "Accept: application/vnd.github.raw",
                f"repos/{REPO}/contents/{rel}?ref={tag}")


def read_tgz(tgz: Path) -> dict[str, str]:
    """Map each RELATIVE path found in an npm tarball (members under package/) to its
    text. A path that is absent is left out; check_npm reports it."""
    files = {}
    with tarfile.open(tgz, "r:gz") as tar:
        for rel in RELATIVE:
            try:
                member = tar.extractfile(f"package/{rel}")
            except KeyError:
                member = None
            if member is not None:
                files[rel] = member.read().decode("utf-8")
    return files


def fetch_npm(version: str) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        name = tool("npm", "pack", f"{NPM_PACKAGE}@{version}", "--silent",
                    "--pack-destination", tmp, cwd=tmp).strip().splitlines()[-1]
        return read_tgz(Path(tmp) / name)


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


def check_tag(tag: str, from_dir: Path | None) -> list[tuple[str, str]]:
    results = []
    for rel in RELATIVE:
        name = f"tag:{Path(rel).name}"
        try:
            text = (from_dir / Path(rel).name).read_text(encoding="utf-8") if from_dir else fetch_tag(tag, rel)
        except TOOL_ERRORS as exc:
            results.append(("UNREADABLE", f"{name} unreadable ({exc})"))
            continue
        results.append(judge(name, text))
    return results


def check_npm(version: str, tgz: Path | None) -> list[tuple[str, str]]:
    try:
        files = read_tgz(tgz) if tgz else fetch_npm(version)
    except TOOL_ERRORS as exc:
        return [("UNREADABLE", f"npm@{version} unreadable ({exc})")]
    results = []
    for rel in RELATIVE:
        name = f"npm:{Path(rel).name}"
        if rel in files:
            results.append(judge(name, files[rel]))
        else:
            results.append(("UNREADABLE", f"{name} absent: tarball has no package/{rel}"))
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check OMC's newest release for the Codex `type` emission.")
    ap.add_argument("--tag")
    ap.add_argument("--from-dir", type=Path)
    ap.add_argument("--npm-from-tgz", type=Path)
    a = ap.parse_args(argv)
    offline = a.from_dir is not None or a.npm_from_tgz is not None
    do_tag = a.from_dir is not None or not offline
    do_npm = a.npm_from_tgz is not None or not offline

    results: list[tuple[str, str]] = []
    notes: list[str] = []
    tag = a.tag or ("local" if offline else None)
    if tag is None:
        try:
            tag = newest_tag()
        except TOOL_ERRORS as exc:
            results.append(("UNREADABLE", f"cannot resolve the newest tag ({exc})"))
    version = None
    if do_npm:
        if a.tag:
            version = a.tag.removeprefix("v")
        elif offline:
            version = "local"
        else:
            try:
                version = npm_latest()
            except TOOL_ERRORS as exc:
                results.append(("UNREADABLE", f"cannot resolve npm latest ({exc})"))
            if version and tag and version != tag.removeprefix("v"):
                notes.append(f"npm latest {version} != newest tag {tag}")

    if do_tag and tag:
        results += check_tag(tag, a.from_dir)
    if do_npm and version:
        results += check_npm(version, a.npm_from_tgz)

    label = " ".join(x for x in [tag and f"tag={tag}" if do_tag else None,
                                 version and f"npm={version}" if do_npm else None] if x)
    detail = "; ".join([d for _, d in results] + [f"note: {n}" for n in notes])
    verdicts = {v for v, _ in results}
    # EMITS outranks UNREADABLE: one file proven to emit is already a definite answer.
    if "EMITS" in verdicts:
        print(f"UPSTREAM: EMITS {label} — {detail}")
        return 1
    if "UNREADABLE" in verdicts or not results:
        print(f"UPSTREAM: UNREADABLE {label} — {detail or 'nothing checked'}")
        return 2
    print(f"UPSTREAM: FIXED {label} — {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
