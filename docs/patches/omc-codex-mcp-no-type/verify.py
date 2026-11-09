#!/usr/bin/env python3
"""Verify omc-codex-mcp-no-type is still applied to every installed OMC copy.

Exit 0: patched everywhere, and the plugin's own renderer emits no `type` line.
Exit 1: patch MISSING somewhere; re-apply with apply.py (see README).
Exit 2: could not judge (no OMC found, a file unreadable, the render probe failed).
         That is not a pass.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from targets import MARKER, ORIGINAL, roots, targets  # noqa: E402

PROBE = r"""
const m = await import(process.argv[1]);
const block = m.renderManagedCodexMcpBlock({
  s: { command: "npx", args: ["-y", "x"], type: "stdio" },
  h: { url: "http://127.0.0.1:9/mcp", type: "http" },
});
process.stdout.write(JSON.stringify({ typeLines: (block.match(/^type\s*=/mg) || []).length,
                                      servers: (block.match(/^\[mcp_servers\./mg) || []).length }));
"""


def main() -> int:
    paths = targets()
    if not paths:
        print("VERIFY: UNREADABLE no installed OMC copy found")
        return 2
    missing, unreadable = [], []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            unreadable.append(str(path))
            continue
        if ORIGINAL.search(text) or MARKER not in text:
            missing.append(str(path))
    # Behavioural check on every dist copy: the real renderer, fed entries that carry
    # `type`, must produce both server blocks and zero `type` lines. A positive
    # control is implicit: `servers == 2` proves the probe rendered something.
    for root in roots():
        dist = root / "dist/installer/mcp-registry.js"
        if not dist.exists():
            continue
        try:
            out = subprocess.run(["node", "--input-type=module", "-e", PROBE, str(dist)],
                                 capture_output=True, text=True, timeout=30)
            res = json.loads(out.stdout)
        except (OSError, ValueError, subprocess.SubprocessError):
            unreadable.append(f"{dist} (render probe failed)")
            continue
        if res.get("servers") != 2:
            unreadable.append(f"{dist} (render probe rendered {res.get('servers')} servers)")
        elif res.get("typeLines") != 0:
            missing.append(f"{dist} (renderer still emits {res['typeLines']} type lines)")
    if missing:
        print("VERIFY: MISSING " + "; ".join(missing))
        return 1
    if unreadable:
        print("VERIFY: UNREADABLE " + "; ".join(unreadable))
        return 2
    print(f"VERIFY: OK files={len(paths)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
