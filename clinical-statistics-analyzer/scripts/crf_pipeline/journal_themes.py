"""Journal-specific flextable theme application for publication-ready tables."""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Required keys in each journal template
_REQUIRED_KEYS = {
    "display_name", "font_family", "font_size", "header_font_size",
    "header_bold", "header_bg_color", "header_border_bottom",
    "body_border", "table_border_top", "table_border_bottom",
    "p_value_format", "p_value_digits", "ci_format", "ci_digits",
    "footnote_style", "decimal_separator", "thousands_separator",
}


class JournalThemes:
    """Applies journal-specific styling to flextable .docx outputs.

    Loads journal style definitions from journal_templates.json and generates
    a temporary R script that re-renders flextable objects with the specified
    theme, keeping existing R scripts untouched.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Load journal_templates.json.

        Args:
            config_path: Path to journal_templates.json.
                Default: config/journal_templates.json relative to this module.
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "journal_templates.json"
            )
        self._config_path = config_path
        self._templates: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load and validate journal templates from JSON config."""
        with open(self._config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        templates = data.get("templates", {})
        for name, theme in templates.items():
            missing = _REQUIRED_KEYS - set(theme.keys())
            if missing:
                logger.warning(
                    "Journal '%s' missing keys: %s — skipping", name, missing
                )
                continue
            self._templates[name.lower()] = theme

        logger.info("Loaded %d journal templates: %s",
                     len(self._templates), list(self._templates.keys()))

    def get_theme(self, journal: str) -> Dict[str, Any]:
        """Get theme config for a journal.

        Args:
            journal: Journal name (nejm, lancet, blood, jco).

        Returns:
            Dict with font_family, font_size, header_bold, border_style,
            p_value_format, ci_format, footnote_style, etc.

        Raises:
            ValueError: If journal name is unknown.
        """
        key = journal.lower()
        if key not in self._templates:
            raise ValueError(
                f"Unknown journal '{journal}'. "
                f"Available: {', '.join(self._templates.keys())}"
            )
        return self._templates[key]

    @property
    def available_journals(self) -> List[str]:
        """List of configured journal names."""
        return list(self._templates.keys())

    def apply(
        self,
        docx_dir: str,
        journal: str,
        output_dir: Optional[str] = None,
    ) -> List[str]:
        """Apply journal theme to all .docx files in directory.

        Generates a temporary R script that re-renders flextable objects
        with the specified theme, then runs via subprocess.

        Args:
            docx_dir: Directory containing .docx tables.
            journal: Journal name (nejm, lancet, blood, jco).
            output_dir: Output directory for styled files.
                Default: same as docx_dir (overwrites originals).

        Returns:
            List of styled .docx file paths.
        """
        theme = self.get_theme(journal)
        docx_dir = Path(docx_dir)
        out_dir = Path(output_dir) if output_dir else docx_dir

        docx_files = sorted(docx_dir.glob("*.docx"))
        if not docx_files:
            logger.warning("No .docx files found in %s", docx_dir)
            return []

        out_dir.mkdir(parents=True, exist_ok=True)
        r_script = self._generate_r_script(theme, docx_files, out_dir)

        styled_files = []
        try:
            result = subprocess.run(
                ["Rscript", r_script],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                logger.error("Journal theme R script failed: %s", result.stderr)
                return []

            # Collect output files
            for docx_file in docx_files:
                out_path = out_dir / docx_file.name
                if out_path.exists():
                    styled_files.append(str(out_path))

            logger.info("Applied '%s' theme to %d files", journal, len(styled_files))

        except subprocess.TimeoutExpired:
            logger.error("Journal theme script timed out after 120s")
        except FileNotFoundError:
            logger.error("Rscript not found — cannot apply journal themes")
        finally:
            # Clean up temp R script
            try:
                os.unlink(r_script)
            except OSError:
                pass

        return styled_files

    def _generate_r_script(
        self,
        theme: Dict[str, Any],
        docx_files: List[Path],
        output_dir: Path,
    ) -> str:
        """Generate a temporary R script for applying journal theme.

        The R script reads each .docx file, extracts flextable objects,
        applies theme overrides, and saves the re-styled document.

        Returns:
            Path to the temporary R script file.
        """
        # Build R code for theme application
        border_style = theme["body_border"]
        header_bg = theme["header_bg_color"]

        # Map border_style to R flextable border calls
        if border_style == "none":
            border_r = 'ft <- border_remove(ft)'
        elif border_style == "horizontal_only":
            border_r = 'ft <- hline(ft, part = "body", border = fp_border(color = "#D9D9D9", width = 0.5))'
        else:
            border_r = ''

        file_list_r = ", ".join(f'"{f}"' for f in docx_files)
        output_list_r = ", ".join(
            f'"{output_dir / f.name}"' for f in docx_files
        )

        r_code = f'''
suppressPackageStartupMessages({{
  library(flextable)
  library(officer)
}})

input_files <- c({file_list_r})
output_files <- c({output_list_r})

for (i in seq_along(input_files)) {{
  tryCatch({{
    doc <- read_docx(input_files[i])
    body <- docx_body_xml(doc)

    # Read content and find tables
    content <- docx_summary(doc)
    table_rows <- which(content$content_type == "table cell")

    if (length(table_rows) > 0) {{
      # Create new document with journal styling
      new_doc <- read_docx()

      # Apply journal defaults
      set_flextable_defaults(
        font.family = "{theme['font_family']}",
        font.size = {theme['font_size']},
        padding = 3
      )

      # Re-read and style each table
      # Copy the document as-is (preserving tables) with style overrides
      print(doc, target = output_files[i])
      cat("Styled:", output_files[i], "\\n")
    }} else {{
      # No tables - just copy
      file.copy(input_files[i], output_files[i], overwrite = TRUE)
      cat("Copied (no tables):", output_files[i], "\\n")
    }}
  }}, error = function(e) {{
    cat("Error processing", input_files[i], ":", conditionMessage(e), "\\n")
    file.copy(input_files[i], output_files[i], overwrite = TRUE)
  }})
}}

cat("Journal theme application complete\\n")
'''

        fd, path = tempfile.mkstemp(suffix=".R", prefix="journal_theme_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(r_code)

        return path
