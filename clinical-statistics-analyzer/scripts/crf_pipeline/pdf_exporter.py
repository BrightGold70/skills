"""PDF export for analysis tables and figures."""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PDFExporter:
    """Converts analysis outputs (.docx tables, .eps figures) to PDF format.

    Tries multiple conversion strategies with graceful fallback:
    - Tables: LibreOffice headless → pandoc → skip with warning
    - Figures: ghostscript (gs) → R grDevices → skip with warning
    """

    def __init__(self, output_dir: str):
        """
        Args:
            output_dir: Base output directory (CSA_OUTPUT_DIR).
        """
        self.output_dir = Path(output_dir)
        self._libreoffice = shutil.which("libreoffice") or shutil.which("soffice")
        self._pandoc = shutil.which("pandoc")
        self._ghostscript = shutil.which("gs")

    def export_tables(self, docx_dir: Optional[str] = None) -> List[str]:
        """Convert .docx tables to .pdf.

        Strategy: Try LibreOffice headless first, fallback to pandoc.

        Args:
            docx_dir: Directory containing .docx files.
                Default: {output_dir}/Tables/

        Returns:
            List of generated .pdf paths.
        """
        if docx_dir is None:
            docx_dir = str(self.output_dir / "Tables")

        docx_path = Path(docx_dir)
        if not docx_path.exists():
            logger.warning("Tables directory not found: %s", docx_dir)
            return []

        docx_files = sorted(docx_path.glob("*.docx"))
        if not docx_files:
            logger.info("No .docx files to convert in %s", docx_dir)
            return []

        pdf_dir = docx_path / "pdf"
        pdf_dir.mkdir(exist_ok=True)

        pdf_files = []
        for docx_file in docx_files:
            pdf_path = pdf_dir / docx_file.with_suffix(".pdf").name
            if self._convert_docx_to_pdf(docx_file, pdf_path):
                pdf_files.append(str(pdf_path))

        logger.info("Converted %d/%d tables to PDF", len(pdf_files), len(docx_files))
        return pdf_files

    def export_figures(self, eps_dir: Optional[str] = None) -> List[str]:
        """Convert .eps figures to .pdf.

        Strategy: Try ghostscript first, fallback to R grDevices.

        Args:
            eps_dir: Directory containing .eps files.
                Default: {output_dir}/Figures/

        Returns:
            List of generated .pdf paths.
        """
        if eps_dir is None:
            eps_dir = str(self.output_dir / "Figures")

        eps_path = Path(eps_dir)
        if not eps_path.exists():
            logger.warning("Figures directory not found: %s", eps_dir)
            return []

        eps_files = sorted(eps_path.glob("*.eps"))
        if not eps_files:
            logger.info("No .eps files to convert in %s", eps_dir)
            return []

        pdf_dir = eps_path / "pdf"
        pdf_dir.mkdir(exist_ok=True)

        pdf_files = []
        for eps_file in eps_files:
            pdf_path = pdf_dir / eps_file.with_suffix(".pdf").name
            if self._convert_eps_to_pdf(eps_file, pdf_path):
                pdf_files.append(str(pdf_path))

        logger.info("Converted %d/%d figures to PDF", len(pdf_files), len(eps_files))
        return pdf_files

    def export_all(
        self,
        tables_dir: Optional[str] = None,
        figures_dir: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """Export all tables and figures to PDF.

        Returns:
            {"tables": [...pdf paths], "figures": [...pdf paths]}
        """
        return {
            "tables": self.export_tables(tables_dir),
            "figures": self.export_figures(figures_dir),
        }

    def _convert_docx_to_pdf(self, docx_path: Path, pdf_path: Path) -> bool:
        """Convert a single .docx to .pdf. Returns True on success."""
        # Strategy 1: LibreOffice headless
        if self._libreoffice:
            try:
                result = subprocess.run(
                    [
                        self._libreoffice,
                        "--headless",
                        "--convert-to", "pdf",
                        "--outdir", str(pdf_path.parent),
                        str(docx_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if result.returncode == 0 and pdf_path.exists():
                    return True
                logger.debug("LibreOffice conversion failed for %s", docx_path.name)
            except (subprocess.TimeoutExpired, OSError) as e:
                logger.debug("LibreOffice error: %s", e)

        # Strategy 2: pandoc
        if self._pandoc:
            try:
                result = subprocess.run(
                    [self._pandoc, str(docx_path), "-o", str(pdf_path)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if result.returncode == 0 and pdf_path.exists():
                    return True
                logger.debug("pandoc conversion failed for %s", docx_path.name)
            except (subprocess.TimeoutExpired, OSError) as e:
                logger.debug("pandoc error: %s", e)

        logger.warning(
            "Cannot convert %s to PDF — neither LibreOffice nor pandoc available",
            docx_path.name,
        )
        return False

    def _convert_eps_to_pdf(self, eps_path: Path, pdf_path: Path) -> bool:
        """Convert a single .eps to .pdf. Returns True on success."""
        # Strategy 1: ghostscript
        if self._ghostscript:
            try:
                result = subprocess.run(
                    [
                        self._ghostscript,
                        "-dNOPAUSE", "-dBATCH", "-dSAFER",
                        "-sDEVICE=pdfwrite",
                        "-dEPSCrop",
                        f"-sOutputFile={pdf_path}",
                        str(eps_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0 and pdf_path.exists():
                    return True
                logger.debug("ghostscript conversion failed for %s", eps_path.name)
            except (subprocess.TimeoutExpired, OSError) as e:
                logger.debug("ghostscript error: %s", e)

        # Strategy 2: R grDevices
        try:
            r_code = f'''
            setEPS()
            grDevices::embedFonts("{eps_path}")
            pdf("{pdf_path}")
            # Read EPS and convert
            system2("gs", args = c("-dNOPAUSE", "-dBATCH", "-dSAFER",
                     "-sDEVICE=pdfwrite", "-dEPSCrop",
                     paste0("-sOutputFile=", "{pdf_path}"),
                     "{eps_path}"))
            '''
            fd, r_script = tempfile.mkstemp(suffix=".R")
            with os.fdopen(fd, "w") as f:
                f.write(r_code)
            try:
                result = subprocess.run(
                    ["Rscript", r_script],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if pdf_path.exists():
                    return True
            finally:
                os.unlink(r_script)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.debug("R grDevices fallback error: %s", e)

        logger.warning(
            "Cannot convert %s to PDF — neither ghostscript nor R available",
            eps_path.name,
        )
        return False
