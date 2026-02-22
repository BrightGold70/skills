#!/usr/bin/env python3
"""
Convert patent specification HTML to PDF for online filing or review.
Uses Playwright (Chromium) for high-fidelity rendering, supporting complex CSS and fonts.
Usage:
  python html_to_pdf.py <input.html> -o <output.pdf>
"""

import argparse
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

async def convert_html_to_pdf(html_path: Path, pdf_path: Path):
    """
    Converts HTML to PDF using Playwright.
    Sets margins according to Chinese patent standards:
    Top/Left: 25mm, Bottom/Right: 15mm.
    """
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Resolve absolute path for file:// protocol
        abs_html_path = html_path.resolve()
        
        # Navigate to the HTML file
        try:
            await page.goto(f"file://{abs_html_path}", wait_until="networkidle")
        except Exception as e:
            print(f"Error loading HTML: {e}", file=sys.stderr)
            await browser.close()
            return 1

        # Generate PDF with specific margins
        # Patent standards: Left/Top >= 25mm, Right/Bottom >= 15mm
        await page.pdf(
            path=str(pdf_path),
            format="A4",
            margin={
                "top": "25mm",
                "left": "25mm",
                "bottom": "15mm",
                "right": "15mm"
            },
            print_background=True,
            display_header_footer=False
        )
        
        await browser.close()
        print(f"Successfully wrote PDF to: {pdf_path}")
        return 0

def main():
    parser = argparse.ArgumentParser(
        description="Convert patent specification HTML to PDF using Playwright."
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
        help="Output PDF file path",
    )
    
    args = parser.parse_args()
    
    if not args.input_html.is_file():
        print(f"Error: input file not found: {args.input_html}", file=sys.stderr)
        sys.exit(1)
        
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Run the async conversion
    exit_code = asyncio.run(convert_html_to_pdf(args.input_html, args.output))
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
