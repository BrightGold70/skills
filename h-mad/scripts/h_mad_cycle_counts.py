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

_VERSION_RE = re.compile(r"\.v(\d+)\.md$")


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


def _discover_artifacts(
    docs_root: Path,
    feature: str,
    pattern: str,
    live_roots: tuple[Path, ...],
    *,
    include_archive: bool,
) -> dict[int, Path]:
    artifacts: dict[int, Path] = {}
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
            artifacts[version] = candidate
    return artifacts


def audit_artifacts(
    docs_root: Path,
    feature: str,
    phase: str,
    *,
    include_archive: bool = True,
) -> dict[int, Path]:
    """Map cycle number to audit file for one phase."""
    segment = PHASE_SEGMENTS.get(phase)
    if segment is None:
        return {}
    return _discover_artifacts(
        docs_root,
        feature,
        f"{feature}.{segment}.audit.v*.md",
        (Path("01-plan/features"), Path("02-design/features")),
        include_archive=include_archive,
    )


def analysis_artifacts(
    docs_root: Path,
    feature: str,
    *,
    include_archive: bool = True,
) -> dict[int, Path]:
    """Map cycle number to versioned gap-analysis file."""
    return _discover_artifacts(
        docs_root,
        feature,
        f"{feature}.analysis.v*.md",
        (Path("03-analysis"),),
        include_archive=include_archive,
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
