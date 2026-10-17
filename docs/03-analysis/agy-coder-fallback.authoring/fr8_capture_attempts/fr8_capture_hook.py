#!/usr/bin/env python3
"""FR-8 step 1 temporary capture hook: store stdin verbatim, allow. Deleted after capture."""
import json, sys, time
from pathlib import Path
raw = sys.stdin.buffer.read()
out = Path(__file__).resolve().parents[1] / "captures"
out.mkdir(exist_ok=True)
try:
    name = json.loads(raw).get("toolCall", {}).get("name", "unknown")
except Exception:
    name = "unparsed"
(out / f"{name}-{time.time_ns()}.json").write_bytes(raw)
print(json.dumps({"decision": "allow"}))
