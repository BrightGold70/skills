#!/usr/bin/env python3
"""
Convert patent specification HTML to docx for online filing.
Uses pandoc; runs from the HTML file's directory so relative image paths resolve.
Usage:
  python html_to_docx.py <input.html> -o <output.docx>
  python html_to_docx.py <input.html> -o <output.docx> --reference-doc=templates/reference.docx
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def find_pandoc() -> str | None:
    return shutil.which("pandoc")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert patent specification HTML to docx (requires pandoc)."
    )
    parser.add_argument(
        "input_html",
        type=Path,
        help="Input HTML file path",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output docx file path",
    )
    parser.add_argument(
        "--reference-doc",
        type=Path,
        default=None,
        help="Optional reference .docx for styling (e.g. templates/reference.docx)",
    )
    args = parser.parse_args()

    pandoc = find_pandoc()
    if not pandoc:
        # Check common paths if not in PATH
        common_paths = ["/usr/bin/pandoc", "/usr/local/bin/pandoc", "/opt/homebrew/bin/pandoc"]
        for p in common_paths:
            if Path(p).exists():
                pandoc = p
                break
    
    if not pandoc:
        print("Error: pandoc not found. Please install pandoc to convert HTML to docx.", file=sys.stderr)
        print("  Installation guide: https://pandoc.org/installing.html", file=sys.stderr)
        print("  On Ubuntu/Debian: sudo apt-get install pandoc", file=sys.stderr)
        return 1

    html_path = args.input_html.resolve()
    if not html_path.is_file():
        print(f"Error: input file not found: {html_path}", file=sys.stderr)
        return 1

    out_path = args.output.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Use default reference doc if exists and not provided
    reference_doc = args.reference_doc
    if reference_doc is None:
        default_ref = Path(__file__).parent.parent / "templates" / "reference.docx"
        if default_ref.exists():
            reference_doc = default_ref

    cmd = [
        str(pandoc),
        "-s",
        str(html_path),
        "-o",
        str(out_path),
    ]
    if reference_doc is not None:
        ref = Path(reference_doc)
        if not ref.is_absolute():
            ref = html_path.parent / ref
        if ref.is_file():
            cmd.extend(["--reference-doc", str(ref)])
        else:
            print(f"Warning: reference-doc not found, skipping: {ref}", file=sys.stderr)

    # Run pandoc from HTML's directory so relative paths (e.g. images/) resolve
    cwd = str(html_path.parent)
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print("Error: pandoc failed.", file=sys.stderr)
        return 1
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
