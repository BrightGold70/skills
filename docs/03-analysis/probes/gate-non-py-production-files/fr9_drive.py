"""FR-9 probe entry point; refusal behaviour is implemented during GREEN."""
from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=("fixture", "replay"))
    parser.add_argument("--side", required=True, choices=("after", "before"))
    parser.add_argument("--host", required=True, choices=("claude", "codex", "agy"))
    parser.add_argument("--out", required=True)
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
