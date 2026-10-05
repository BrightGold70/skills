#!/usr/bin/env python3
"""Is this lane quiet? Read its claims against four clocks.

The heartbeat alone has misread a working lane as dead four times across two
repos (skill-candidates row "gate-on-two-independent-clocks"). This prints the
reading `h_mad_state_ownership.liveness_evidence` makes from the heartbeat, the
owner's transcript mtime, the lane's newest commit and `ps` argv, before anyone
releases, force-claims or declares the lane idle.

Usage:
  h_mad_lane_liveness.py <lane> [--feature F]

`<lane>` is a worktree holding `docs/.bkit-memory.json`. One line per claimed
feature (or for `--feature F` alone), each ending ` feature=<F>`:

  LIVENESS: LIVE evidence=<ps|transcript:Ns|commit:Ns|heartbeat:Ns,...> heartbeat_age=Ns
  LIVENESS: QUIET heartbeat_age=Ns transcript_age=Ns commit_age=Ns window=Ns
  LIVENESS: UNKNOWN reason=<clock,...>

`reason=state` (the state file is missing or unreadable) and `reason=no-such-feature`
are UNKNOWN too: "could not check" never reads as QUIET. A lane holding no claim at
all prints `LIVENESS: NONE reason=no-claim` — nothing failed to read. Read-only; exit 0.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h_mad_state_ownership  # noqa: E402

STATE = Path("docs") / ".bkit-memory.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("lane", type=Path)
    ap.add_argument("--feature")
    args = ap.parse_args(argv)

    try:
        data = json.loads((args.lane / STATE).read_text(encoding="utf-8"))
        records = data.get("orchestrator_state") or {}
        if not isinstance(records, dict):
            raise ValueError("orchestrator_state is not an object")
    except (OSError, UnicodeDecodeError, ValueError, AttributeError) as exc:
        print(f"LIVENESS: UNKNOWN reason=state lane={args.lane} — {exc}")
        return 0

    if args.feature:
        if not isinstance(records.get(args.feature), dict):
            print(f"LIVENESS: UNKNOWN reason=no-such-feature feature={args.feature}")
            return 0
        features = [args.feature]
    else:
        features = [f for f, r in sorted(records.items())
                    if isinstance(r, dict) and r.get("owner_session_id")]
        if not features:
            print(f"LIVENESS: NONE reason=no-claim lane={args.lane}")
            return 0
    for feature in features:
        line = h_mad_state_ownership.liveness_evidence(records[feature], args.lane)
        print(f"{line} feature={feature}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
