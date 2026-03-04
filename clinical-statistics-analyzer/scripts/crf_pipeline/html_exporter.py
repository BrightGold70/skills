"""Interactive HTML dashboard generator using rmarkdown + plotly + DT."""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HTMLExporter:
    """Generates self-contained interactive HTML dashboards.

    Creates an R Markdown (.Rmd) document with Plotly interactive KM curves
    and DT filterable tables, then renders to a self-contained HTML file.
    """

    def __init__(self, output_dir: str, disease: str):
        """
        Args:
            output_dir: Base output directory.
            disease: Disease type for dashboard customization.
        """
        self.output_dir = Path(output_dir)
        self.disease = disease
        self._reports_dir = self.output_dir / "Reports"
        self._reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, csv_path: str, script_results: list) -> str:
        """Generate self-contained HTML dashboard.

        Creates an R Markdown document with interactive visualizations,
        then renders via rmarkdown::render() to self-contained HTML.

        Args:
            csv_path: Path to transformed R-ready CSV.
            script_results: Results for metadata (which scripts ran).

        Returns:
            Path to generated Dashboard_{disease}.html file,
            or empty string on failure.
        """
        rmd_path = self._create_rmd_template(csv_path)
        html_path = self._render_html(rmd_path)

        # Clean up temp .Rmd
        try:
            os.unlink(rmd_path)
        except OSError:
            pass

        return html_path

    def _create_rmd_template(self, csv_path: str) -> str:
        """Generate the .Rmd template with embedded R code chunks.

        Returns:
            Path to temporary .Rmd file.
        """
        disease_upper = self.disease.upper()
        output_path = self._reports_dir / f"Dashboard_{disease_upper}.html"

        rmd_content = f'''---
title: "{disease_upper} Clinical Trial Dashboard"
output:
  html_document:
    self_contained: true
    theme: flatly
    toc: true
    toc_float: true
    code_folding: hide
---

```{{r setup, include=FALSE}}
knitr::opts_chunk$set(echo = FALSE, warning = FALSE, message = FALSE)
library(plotly)
library(DT)
library(dplyr)
library(survival)
library(survminer)
```

## Study Overview

```{{r load-data}}
df <- read.csv("{csv_path}", stringsAsFactors = FALSE)
n_patients <- nrow(df)
n_cols <- ncol(df)
```

**Dataset**: `r n_patients` patients, `r n_cols` variables

---

## Baseline Characteristics

```{{r baseline-table}}
# Select key baseline columns
baseline_cols <- intersect(
  c("Patient_ID", "Age", "Sex", "Treatment", "OS_months", "OS_status"),
  names(df)
)
if (length(baseline_cols) > 0) {{
  DT::datatable(
    df[, baseline_cols, drop = FALSE],
    filter = "top",
    options = list(pageLength = 10, scrollX = TRUE),
    caption = "Baseline Characteristics (filterable)"
  )
}}
```

## Survival Analysis

```{{r km-plotly}}
if (all(c("OS_months", "OS_status") %in% names(df))) {{
  surv_obj <- Surv(df$OS_months, df$OS_status)

  if ("Treatment" %in% names(df)) {{
    km_fit <- survfit(surv_obj ~ Treatment, data = df)
  }} else {{
    km_fit <- survfit(surv_obj ~ 1, data = df)
  }}

  # Extract KM data for plotly
  km_data <- data.frame(
    time = km_fit$time,
    surv = km_fit$surv,
    upper = km_fit$upper,
    lower = km_fit$lower,
    n.risk = km_fit$n.risk,
    n.event = km_fit$n.event
  )

  if (!is.null(km_fit$strata)) {{
    strata_names <- rep(names(km_fit$strata), km_fit$strata)
    km_data$group <- strata_names
  }} else {{
    km_data$group <- "All"
  }}

  p <- plot_ly()
  for (grp in unique(km_data$group)) {{
    grp_data <- km_data[km_data$group == grp, ]
    p <- p %>%
      add_trace(
        data = grp_data,
        x = ~time, y = ~surv,
        type = "scatter", mode = "lines",
        name = grp,
        text = ~paste0(
          "Time: ", round(time, 1), " mo<br>",
          "Survival: ", round(surv * 100, 1), "%<br>",
          "At risk: ", n.risk, "<br>",
          "Events: ", n.event
        ),
        hoverinfo = "text"
      )
  }}

  p <- p %>%
    layout(
      title = "Kaplan-Meier Survival Curve (Interactive)",
      xaxis = list(title = "Time (months)"),
      yaxis = list(title = "Survival Probability", range = c(0, 1)),
      hovermode = "closest"
    )
  p
}}
```

## Safety Summary

```{{r safety-table}}
# If safety-related columns exist, show filterable table
safety_cols <- grep("(?i)(ae|adverse|toxicity|grade|safety|tox_)", names(df), value = TRUE)
if (length(safety_cols) > 0) {{
  DT::datatable(
    df[, c("Patient_ID", safety_cols), drop = FALSE],
    filter = "top",
    options = list(pageLength = 10, scrollX = TRUE),
    caption = "Safety Data (filterable)"
  )
}} else {{
  cat("No safety columns detected in dataset.")
}}
```

## Data Explorer

```{{r full-data}}
DT::datatable(
  df,
  filter = "top",
  options = list(pageLength = 10, scrollX = TRUE),
  caption = "Full Dataset (filterable, searchable)"
)
```

---

*Generated by clinical-statistics-analyzer v3.1*
'''

        fd, rmd_path = tempfile.mkstemp(
            suffix=".Rmd", prefix=f"dashboard_{self.disease}_"
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(rmd_content)

        return rmd_path

    def _render_html(self, rmd_path: str) -> str:
        """Render .Rmd to self-contained HTML via subprocess Rscript.

        Returns:
            Path to generated .html file, or empty string on failure.
        """
        output_path = self._reports_dir / f"Dashboard_{self.disease.upper()}.html"

        r_cmd = (
            f'rmarkdown::render("{rmd_path}", '
            f'output_file = "{output_path}", '
            f'output_format = rmarkdown::html_document(self_contained = TRUE), '
            f'quiet = TRUE)'
        )

        try:
            result = subprocess.run(
                ["Rscript", "-e", r_cmd],
                capture_output=True,
                text=True,
                timeout=180,  # 3 minutes for rendering
            )

            if result.returncode == 0 and output_path.exists():
                logger.info("Generated HTML dashboard: %s", output_path)
                return str(output_path)
            else:
                logger.error(
                    "rmarkdown::render failed (exit=%d): %s",
                    result.returncode, result.stderr[:500],
                )
                return ""

        except subprocess.TimeoutExpired:
            logger.error("HTML dashboard rendering timed out after 180s")
            return ""
        except FileNotFoundError:
            logger.error("Rscript not found — cannot render HTML dashboard")
            return ""
