#!/usr/bin/env python3
"""
Example: generate a patent figure (block diagram) with code and save to images/.
Use as a template for patent figures; figure labels must be in English (per project rule).
Run from the patent spec directory so images/ is next to the HTML, or set --output-dir.

Usage:
  python scripts/generate_figure_example.py
  python scripts/generate_figure_example.py -o images/图1.png
  python scripts/generate_figure_example.py --output-dir /path/to/spec/images
"""

import argparse
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate example block diagram for patent figure.")
    parser.add_argument("-o", "--output", type=Path, default=Path("images/图1.png"), help="Output image path")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory (file name will be 图1.png)")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for output image")
    args = parser.parse_args()

    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = args.output_dir / "图1.png"
    else:
        out_path = args.output.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(1, 1, figsize=(6, 4))

    # Simple block diagram: Input -> Process -> Output (labels in English)
    boxes = [
        (0.15, 0.5, 0.2, 0.25, "Input"),
        (0.45, 0.5, 0.2, 0.25, "Process"),
        (0.75, 0.5, 0.2, 0.25, "Output"),
    ]
    for x, y, w, h, label in boxes:
        rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", linewidth=1.5, edgecolor="black", facecolor="lightgray")
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=11)

    # Arrows between boxes
    ax.annotate("", xy=(0.45, 0.625), xytext=(0.35, 0.625), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("", xy=(0.75, 0.625), xytext=(0.65, 0.625), arrowprops=dict(arrowstyle="->", lw=1.5))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=args.dpi, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
