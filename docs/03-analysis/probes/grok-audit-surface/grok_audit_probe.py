"""Probe entry point for the Grok audit surface calibration."""

import argparse
import sys
import traceback
from pathlib import Path
from typing import Callable, NoReturn


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "h-mad" / "scripts"))
import h_mad_audit_gate as _gate
import h_mad_audit_cycle as _cycle
from h_mad_audit_origins import ORIGINS
from h_mad_review_evidence import _GROK_TYPES


SOURCES: dict[str, str] = {
    "audit-report-docs-copy": "docs/archive/2026-09",
    "tdd-gate-fail-opens": "docs/archive/2026-09",
    "agy-coder-fallback": "docs/archive/2026-10",
}
GRAMMAR: dict[str, tuple[str, str]] = {
    "check-ledger": ("LEDGER:", "UNREADABLE"),
    "build-root": ("ROOT:", "UNREADABLE"),
    "record-cycle": ("RECORD:", "REFUSED"),
    "commit-data": ("COMMIT:", "REFUSED"),
    "smoke": ("SMOKE:", "UNREADABLE"),
    "extract": ("FINDINGS:", "UNREADABLE"),
    "score": ("SEEDSCORE:", "UNREADABLE"),
    "rescore": ("SEEDSCORE:", "UNREADABLE"),
    "main-leak": ("MAINLEAK:", "UNREADABLE"),
}
MODES: dict[str, Callable[[argparse.Namespace], int]] = {}
_OPEN_INPUT: str | None = None


class ProbeRefusal(Exception):
    """Base for declared refusals, which do not print tracebacks."""


class UsageError(ProbeRefusal):
    """A command line outside the probe's grammar."""


class Refusal(ProbeRefusal):
    """A mode's declared refusal reason."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _TokenArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs) -> None:
        kwargs["add_help"] = False  # M:GAS-NO-HELP
        kwargs["allow_abbrev"] = False  # M:GAS-NO-ABBREV
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> NoReturn:
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        raise UsageError(message)  # M:GAS-USAGE


def parse_sources(value: str) -> dict[str, str]:
    """Parse the synthetic fixtures' ordered source-directory overrides."""
    sources = {}
    for item in value.split(","):
        name, separator, directory = item.partition("=")
        if not separator or not name or not directory or name in sources:
            raise argparse.ArgumentTypeError("expected unique name=archive-dir entries")
        sources[name] = directory
    return sources


def build_parser() -> _TokenArgumentParser:
    parser = _TokenArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", parser_class=_TokenArgumentParser)

    ledger = subparsers.add_parser("check-ledger")
    ledger_input = ledger.add_mutually_exclusive_group(required=True)
    ledger_input.add_argument("--tree", type=Path)
    ledger_input.add_argument("--repo", type=Path)
    ledger.add_argument("--calibration-sha")
    ledger.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    root = subparsers.add_parser("build-root")
    root.add_argument("--repo", type=Path, required=True)
    root.add_argument("--calibration-sha", required=True)
    root.add_argument("--doc", required=True)
    root.add_argument("--purpose", choices=("s1", "s2v1", "s2v2", "rescore"), required=True)
    root.add_argument("--list-commit", default="HEAD")
    root.add_argument("--dest-parent", type=Path)
    root.add_argument("--reset")
    root.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    record = subparsers.add_parser("record-cycle")
    for flag in ("--stem", "--root", "--root-record", "--stdout", "--command", "--dest"):
        record.add_argument(flag, type=Path, required=True)

    commit = subparsers.add_parser("commit-data")
    commit.add_argument("--repo", type=Path, required=True)
    commit.add_argument("--parent", required=True)
    commit.add_argument("--src", type=Path, required=True)
    commit.add_argument("--message", required=True)

    smoke = subparsers.add_parser("smoke")
    smoke.add_argument("--data", type=Path, required=True)
    smoke.add_argument("--vocab-py", type=Path, default=REPO / "h-mad/scripts/h_mad_review_evidence.py")
    smoke.add_argument("--vocab-sh", type=Path, default=REPO / "h-mad/scripts/hmad-dispatch.sh")

    extract = subparsers.add_parser("extract")
    extract_input = extract.add_mutually_exclusive_group(required=True)
    extract_input.add_argument("--tree", type=Path)
    extract_input.add_argument("--repo", type=Path)
    extract.add_argument("--base-sha")
    extract.add_argument("--s2", type=Path, required=True)
    extract.add_argument("--shuffle-seed", type=int, required=True)
    extract.add_argument("--out", type=Path, required=True)
    extract.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    score = subparsers.add_parser("score")
    score.add_argument("--tree", type=Path, required=True)
    score.add_argument("--calibration-sha")
    score.add_argument("--score-sha")
    score.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    rescore = subparsers.add_parser("rescore")
    rescore.add_argument("--repo", type=Path, required=True)
    rescore.add_argument("--calibration-sha", required=True)
    rescore.add_argument("--smoke-sha", required=True)
    rescore.add_argument("--score-sha", required=True)
    rescore.add_argument("--remote", default="origin")
    rescore.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    leak = subparsers.add_parser("main-leak")
    leak.add_argument("--repo", type=Path, required=True)
    leak.add_argument("--calibration-sha", required=True)
    leak.add_argument("--smoke-sha", required=True)
    leak.add_argument("--score-sha")
    leak.add_argument("--remote", default="origin")
    leak.add_argument("--sources", type=parse_sources, default=SOURCES.copy())
    return parser


def refusal_token(mode: str, exc: BaseException, argv: list[str]) -> str:
    prefix, verdict = GRAMMAR[mode]
    if isinstance(exc, Refusal):
        reason = exc.reason
    elif mode == "smoke":
        path = ""
        if _OPEN_INPUT is not None:
            path = _OPEN_INPUT
        else:
            for index, word in enumerate(argv):
                if word == "--data":
                    path = argv[index + 1] if index + 1 < len(argv) else ""
                    break
                if word.startswith("--data="):
                    path = word.partition("=")[2]
                    break
        reason = f"input_unparseable:{path}"
    else:
        reason = f"internal:{type(exc).__name__}"  # M:GAS-LAST-RESORT
    return f"{prefix} {verdict} reason={reason}"


def main(argv: list[str] | None = None) -> int:
    global _OPEN_INPUT
    _OPEN_INPUT = None
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not argv or argv[0] not in GRAMMAR:
        print("PROBE: UNREADABLE reason=unknown_mode")  # M:GAS-UNKNOWN-MODE
        parser.print_usage(sys.stderr)
        print("[H-MAD] grok-audit-surface unknown_mode UNREADABLE", file=sys.stderr)
        return 2
    mode = argv[0]
    try:
        args = parser.parse_args(argv)
        if mode == "check-ledger" and (args.repo is not None) != (args.calibration_sha is not None):
            parser.error("--repo and --calibration-sha must be supplied together")
        if mode == "extract" and (args.repo is not None) != (args.base_sha is not None):
            parser.error("--repo and --base-sha must be supplied together")
        if mode == "score" and (args.calibration_sha is None) != (args.score_sha is None):
            parser.error("--calibration-sha and --score-sha must be supplied together")
        return MODES[mode](args)
    except Exception as exc:
        if not isinstance(exc, ProbeRefusal):  # M:GAS-TRACEBACK-SCOPE
            traceback.print_exc(file=sys.stderr)
        print(refusal_token(mode, exc, argv))
        print(f"[H-MAD] grok-audit-surface {mode} {GRAMMAR[mode][1]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
