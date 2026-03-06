"""
bootstrap_notebooks.py — One-time setup for the open-notebook Hematology Guidelines notebook.

Run once after deploying open-notebook to create the single shared notebook and ingest
the public guideline URLs listed in GUIDELINE_SOURCES below.

Usage:
    python bootstrap_notebooks.py [--base-url http://localhost:5055] [--dry-run]
    python bootstrap_notebooks.py --check              # verify existing config + server
    python bootstrap_notebooks.py --local-pdf path.pdf # ingest a local PDF

On success this writes notebooklm_config.json next to this script.
That file is gitignored and is read at runtime by StatisticalBridge._load_nlm_config().
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# --------------------------------------------------------------------------- #
# Guideline sources — public DOIs / URLs for ingestion
# --------------------------------------------------------------------------- #
NOTEBOOK_NAME = "Hematology Guidelines"
NOTEBOOK_DESCRIPTION = (
    "ELN 2022 AML, ELN 2020/2025 CML, NIH cGVHD 2014, CTCAE v5, "
    "BOIN dose-finding — curated hematology guidelines for HPW enrichment."
)

GUIDELINE_SOURCES = [
    {
        "name": "ELN 2022 AML Risk Stratification & Response Criteria",
        "url": "https://doi.org/10.1182/blood.2022016867",
    },
    {
        "name": "ELN 2020 CML Recommendations (BCR::ABL1 milestones)",
        "url": "https://doi.org/10.1038/s41375-020-0776-2",
    },
    {
        "name": "NIH 2014 Consensus: Chronic GVHD Biology & Diagnosis",
        "url": "https://doi.org/10.1182/blood-2014-12-580605",
    },
    {
        "name": "CTCAE v5.0 — NCI Adverse Event Grading",
        "url": "https://ctep.cancer.gov/protocoldevelopment/electronic_applications/ctc.htm",
    },
    {
        "name": "BOIN Dose-Finding Design (Liu & Yuan 2015)",
        "url": "https://doi.org/10.1111/rssc.12089",
    },
]

CONFIG_PATH = Path(__file__).parent / "notebooklm_config.json"


# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #

def _load_integration(base_url: str):
    try:
        from tools.notebooklm_integration import NotebookLMIntegration
    except ImportError:
        print("ERROR: Could not import NotebookLMIntegration. Run from HPW root with venv active.")
        sys.exit(1)
    return NotebookLMIntegration(base_url=base_url)


# --------------------------------------------------------------------------- #
# Check mode
# --------------------------------------------------------------------------- #

def check(base_url: str) -> None:
    """Verify existing config and server reachability."""
    nlm = _load_integration(base_url)

    print(f"Server: {base_url}")
    ok = nlm.health_check()
    print(f"  Health check: {'OK' if ok else 'FAILED — server not reachable'}")

    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            print(f"\nConfig: {CONFIG_PATH}")
            print(f"  base_url:    {cfg.get('base_url', '(missing)')}")
            print(f"  notebook_id: {cfg.get('notebook_id', '(missing)')}")
        except json.JSONDecodeError:
            print(f"\nConfig: {CONFIG_PATH} — INVALID JSON")
    else:
        print(f"\nConfig: {CONFIG_PATH} — NOT FOUND (run without --check to bootstrap)")

    sys.exit(0 if ok else 1)


# --------------------------------------------------------------------------- #
# Bootstrap logic
# --------------------------------------------------------------------------- #

def bootstrap(
    base_url: str,
    dry_run: bool = False,
    local_pdfs: list[str] | None = None,
) -> None:
    nlm = _load_integration(base_url)

    print(f"Checking open-notebook at {base_url} ...")
    if not dry_run and not nlm.health_check():
        print("ERROR: open-notebook server is not reachable. Start it with docker-compose up -d")
        sys.exit(1)
    print("  Server OK" if not dry_run else "  [dry-run] skipped health check")

    # Create notebook
    print(f"\nCreating notebook: '{NOTEBOOK_NAME}' ...")
    if dry_run:
        notebook_id = "DRY-RUN-NOTEBOOK-ID"
        print(f"  [dry-run] notebook_id = {notebook_id}")
    else:
        notebook_id = nlm.create_notebook(NOTEBOOK_NAME, NOTEBOOK_DESCRIPTION)
        if not notebook_id:
            print("ERROR: Failed to create notebook. Check server logs.")
            sys.exit(1)
        print(f"  Created: {notebook_id}")

    # Ingest URL sources
    all_sources = list(GUIDELINE_SOURCES)
    # Append local PDFs as source entries
    for pdf_path in (local_pdfs or []):
        all_sources.append({"name": Path(pdf_path).name, "url": None, "local_path": pdf_path})

    print(f"\nIngesting {len(all_sources)} guideline sources ...")
    failed = []
    col_w = max(len(s["name"]) for s in all_sources) + 2

    for i, src in enumerate(all_sources, start=1):
        name = src["name"]
        local_path = src.get("local_path")

        if dry_run:
            kind = f"[file] {local_path}" if local_path else f"[url]  {src['url']}"
            print(f"  [{i:2}/{len(all_sources)}] [dry-run]  {name:<{col_w}}  {kind}")
            continue

        if local_path:
            ok = nlm.add_source_file(notebook_id, local_path)
        else:
            ok = nlm.add_source_url(notebook_id, src["url"])

        status = "OK    " if ok else "FAILED"
        print(f"  [{i:2}/{len(all_sources)}] {status}  {name}")
        if not ok:
            failed.append(name)
        time.sleep(0.5)

    # Write config
    config = {"base_url": base_url, "notebook_id": notebook_id}
    if not dry_run:
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print(f"\nWritten: {CONFIG_PATH}")
    else:
        print(f"\n[dry-run] Would write to {CONFIG_PATH}:")
        print(json.dumps(config, indent=2))

    # Summary
    print("\n" + "=" * 60)
    if failed:
        print(f"WARNING: {len(failed)} source(s) failed to ingest:")
        for name in failed:
            print(f"  - {name}")
        print("You can retry them manually via the open-notebook UI at http://localhost:8502")
    else:
        print("Bootstrap complete. All sources ingested successfully.")
    print(f"Notebook ID: {notebook_id}")
    print("=" * 60)


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap the Hematology Guidelines notebook in open-notebook.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python bootstrap_notebooks.py                        # bootstrap (default)\n"
            "  python bootstrap_notebooks.py --check               # verify existing setup\n"
            "  python bootstrap_notebooks.py --local-pdf ELN.pdf   # add a local PDF\n"
            "  python bootstrap_notebooks.py --dry-run             # preview without HTTP calls"
        ),
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:5055",
        help="Base URL of the open-notebook server (default: http://localhost:5055)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify existing notebooklm_config.json and server reachability, then exit.",
    )
    parser.add_argument(
        "--local-pdf",
        dest="local_pdfs",
        action="append",
        metavar="PATH",
        default=[],
        help="Path to a local PDF to ingest (may be repeated for multiple files).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making any HTTP requests.",
    )
    args = parser.parse_args()

    if args.check:
        check(base_url=args.base_url)
    else:
        bootstrap(
            base_url=args.base_url,
            dry_run=args.dry_run,
            local_pdfs=args.local_pdfs,
        )


if __name__ == "__main__":
    main()
