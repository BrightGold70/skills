#!/usr/bin/env python3
"""Derive H-MAD audit and implementation cycle counts from documentation files."""
from __future__ import annotations

import re
from pathlib import Path


PHASE_SEGMENTS: dict[str, str] = {
    "plan": "plan",
    "design": "design",
    "impl_plan": "impl-plan",
}

# Every other h-mad surface spells the phase with a dash (`h_mad_assemble_audit.PHASES`,
# `h_mad_audit_cycle`'s `--phase` choices), while the keys above use an underscore
# because they are also state-file field names. A caller passing the codebase's own
# spelling got `{}` back -- indistinguishable from "no audits were run". Accept both
# and keep a genuinely unknown phase empty.
_PHASE_ALIASES: dict[str, str] = {
    segment: key for key, segment in PHASE_SEGMENTS.items() if segment != key
}

# One optional discriminator token after the cycle number, taken from the corpus
# rather than invented: over 1120 real audit files the token is one of `''`, `.p1`,
# `.p2`, `.p3`, `.codex`, `.agy`, `.claude` -- always exactly one, and a pass index
# never co-occurs with a surface name.
#
# `.p<i>` is the per-pass artifact `audit-cycle` writes; the surface names are
# written by whoever ran the audit. Both passes and both surfaces carry the SAME
# v-number, and callers key the result by that int, so they collapse to one cycle.
# Without the `.p<i>` half the counter reported 0 for a feature with 24 real audit
# cycles; without the surface half it reported a cycle eight behind the newest, and
# `h_mad_do_preconditions` printed `PRECONDITION: PASS` off that stale report.
#
# The token is deliberately open rather than a `(codex|agy|claude)` alternation: a
# closed set re-creates this exact blindness on the fourth surface, silently. It is
# equally deliberately a SINGLE dot-free token -- `…v26.codex.draft.md` is not an
# audit report, and admitting it hands `_audit_issue` a headingless file at the
# moment the operator is told the gate passed. Too wide is as silent as too narrow.
_VERSION_RE = re.compile(r"\.v(\d+)(?:\.[A-Za-z0-9][A-Za-z0-9_-]*)?\.md$")


def _archive_roots(docs_root: Path, feature: str) -> list[Path]:
    try:
        return list((docs_root / "archive").glob(f"*/{feature}"))
    except OSError:
        return []


def _search_roots(
    docs_root: Path,
    feature: str,
    live_roots: tuple[Path, ...],
    include_archive: bool,
) -> list[Path]:
    roots = [docs_root / relative for relative in live_roots]
    if include_archive:
        roots.extend(_archive_roots(docs_root, feature))
    return roots


def _discover_artifact_groups(
    docs_root: Path,
    feature: str,
    pattern: str,
    live_roots: tuple[Path, ...],
    *,
    include_archive: bool,
) -> dict[int, list[Path]]:
    grouped: dict[int, list[Path]] = {}
    prefix = f"{feature}."
    roots = _search_roots(docs_root, feature, live_roots, include_archive)

    for root in roots:
        try:
            candidates = list(root.glob(pattern))
        except OSError:
            continue
        for candidate in candidates:
            try:
                name = candidate.name
                if not name.startswith(prefix):
                    continue
                match = _VERSION_RE.search(name)
                if match is None:
                    continue
                version = int(match.group(1))
            except (OSError, ValueError):
                continue
            grouped.setdefault(version, []).append(candidate)

    # Sort so that two runs over one tree agree on which artifact represents a
    # cycle. `Path.glob` yields in filesystem order, and 256 of 763 real
    # (feature, phase, version) groups hold more than one file, so the previous
    # `artifacts[version] = candidate` picked arbitrarily among them.
    #
    # Archiving copies an audit rather than moving it, so most cycles are found
    # twice under the same filename -- once live, once under `docs/archive/`.
    # That is one audit, not two: collapse by filename and keep the live copy,
    # which `_search_roots` yields before any archive root. Without this the
    # groups double every archived cycle and a caller scoring them reports each
    # finding twice.
    return {version: _collapse(paths) for version, paths in grouped.items()}


def _collapse(paths: list[Path]) -> list[Path]:
    """Sorted, one entry per filename, live copy preferred over the archived one."""
    by_name: dict[str, Path] = {}
    for path in sorted(paths):
        by_name.setdefault(path.name, path)
    return sorted(by_name.values())


def _representatives(groups: dict[int, list[Path]]) -> dict[int, Path]:
    """One artifact per cycle -- the deterministic first of the sorted group."""
    return {version: paths[0] for version, paths in groups.items()}


def audit_artifact_groups(
    docs_root: Path,
    feature: str,
    phase: str,
    *,
    include_archive: bool = True,
) -> dict[int, list[Path]]:
    """Map cycle number to EVERY audit file recorded for that cycle.

    More than one is the normal case, not an anomaly: `.p1`/`.p2` are two halves
    of one audit's output, and `.codex`/`.agy` at the same cycle are two different
    auditors. Any caller deciding whether a cycle is clean must read all of them --
    reading whichever one the filesystem listed first is "gate on one audit pass"
    wearing a green verdict.
    """
    segment = PHASE_SEGMENTS.get(phase) or PHASE_SEGMENTS.get(
        _PHASE_ALIASES.get(phase, "")
    )
    if segment is None:
        return {}
    return _discover_artifact_groups(
        docs_root,
        feature,
        f"{feature}.{segment}.audit.v*.md",
        (Path("01-plan/features"), Path("02-design/features")),
        include_archive=include_archive,
    )


def audit_artifacts(
    docs_root: Path,
    feature: str,
    phase: str,
    *,
    include_archive: bool = True,
) -> dict[int, Path]:
    """Map cycle number to one representative audit file for one phase."""
    return _representatives(
        audit_artifact_groups(
            docs_root, feature, phase, include_archive=include_archive
        )
    )


def analysis_artifacts(
    docs_root: Path,
    feature: str,
    *,
    include_archive: bool = True,
) -> dict[int, Path]:
    """Map cycle number to versioned gap-analysis file."""
    return _representatives(
        _discover_artifact_groups(
            docs_root,
            feature,
            f"{feature}.analysis.v*.md",
            (Path("03-analysis"),),
            include_archive=include_archive,
        )
    )


def latest_audit_path(
    docs_root: Path,
    feature: str,
    phase: str,
    *,
    include_archive: bool = True,
) -> Path | None:
    """Return the audit file with the highest cycle number, or None."""
    artifacts = audit_artifacts(
        docs_root,
        feature,
        phase,
        include_archive=include_archive,
    )
    if not artifacts:
        return None
    return artifacts[max(artifacts)]


def latest_audit_paths(
    docs_root: Path,
    feature: str,
    phase: str,
    *,
    include_archive: bool = True,
) -> list[Path]:
    """Every audit file at the highest cycle number, sorted; empty when there are none."""
    groups = audit_artifact_groups(
        docs_root,
        feature,
        phase,
        include_archive=include_archive,
    )
    if not groups:
        return []
    return groups[max(groups)]


def audit_cycles(docs_root: Path, feature: str) -> dict[str, int]:
    """Return the maximum audit cycle reached for each phase."""
    return {
        phase: max(audit_artifacts(docs_root, feature, phase), default=0)
        for phase in PHASE_SEGMENTS
    }


def iterate_cycles(docs_root: Path, feature: str) -> int:
    """Return the number of iterations implied by versioned analyses."""
    artifacts = analysis_artifacts(docs_root, feature)
    return max(0, max(artifacts, default=0) - 1)
