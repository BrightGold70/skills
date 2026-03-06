# Script: AML Composite Response Analysis
# Purpose: Construct composite complete response (cCR = CR + CRi + CRh + MLFS) and generate waterfall plot
# Reference: Döhner H et al. Blood 2022 ELN recommendations; Kantarjian et al. JCO 2021
# Usage: Rscript 21_aml_composite_response.R <dataset_path> [cycle_number]
#   dataset_path: CSV/XLSX file with one row per patient, response columns per ELN 2022
#   cycle_number: optional integer label for the assessment cycle (default: 1)

library(dplyr)
library(ggplot2)
library(officer)
library(flextable)
library(readxl)

# ── write_stats_json: emit machine-readable statistics for HPW consumption ────
write_stats_json <- function(
  key_statistics   = list(),
  analysis_notes   = list(),
  disease_specific = list(),
  script_stem      = NULL,
  output_dir       = Sys.getenv("CSA_OUTPUT_DIR")
) {
  if (nchar(output_dir) == 0) {
    message("CSA_OUTPUT_DIR not set; skipping stats JSON"); return(invisible(NULL))
  }
  if (is.null(script_stem)) {
    args_all  <- commandArgs(trailingOnly = FALSE)
    file_arg  <- grep("--file=", args_all, value = TRUE)
    script_stem <- if (length(file_arg) > 0) tools::file_path_sans_ext(basename(sub("--file=", "", file_arg[1]))) else "unknown"
  }
  key_statistics   <- Filter(Negate(is.null), key_statistics)
  disease_specific <- Filter(Negate(is.null), disease_specific)
  payload <- list(key_statistics = key_statistics, analysis_notes = analysis_notes)
  if (length(disease_specific) > 0) payload$disease_specific <- disease_specific
  out_dir  <- file.path(output_dir, "data")
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  out_path <- file.path(out_dir, paste0(script_stem, "_stats.json"))
  jsonlite::write_json(payload, out_path, auto_unbox = TRUE, pretty = TRUE, null = "null")
  message("[write_stats_json] Written: ", out_path)
  invisible(out_path)
}
# ─────────────────────────────────────────────────────────────────────────────

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: Rscript 21_aml_composite_response.R <dataset_path> [cycle_number]")
}

input_data_path <- args[1]
cycle_label     <- ifelse(length(args) >= 2, as.integer(args[2]), 1L)

output_dir  <- Sys.getenv("CSA_OUTPUT_DIR", "")
if (output_dir == "") stop("CSA_OUTPUT_DIR not set. Export it first: export CSA_OUTPUT_DIR=/path/to/output")
tables_dir  <- file.path(output_dir, "Tables")
figures_dir <- file.path(output_dir, "Figures")
if (!dir.exists(tables_dir))  dir.create(tables_dir,  recursive = TRUE)
if (!dir.exists(figures_dir)) dir.create(figures_dir, recursive = TRUE)

# ---------------------------------------------------------------------------
# 1. Load data (CSV or XLSX)
# ---------------------------------------------------------------------------
ext <- tolower(tools::file_ext(input_data_path))
if (ext %in% c("xlsx", "xls")) {
  df <- read_excel(input_data_path)
} else {
  df <- read.csv(input_data_path, stringsAsFactors = FALSE)
}

cat("Loaded", nrow(df), "patients from", input_data_path, "\n")

# ---------------------------------------------------------------------------
# 2. Expected columns (ELN 2022 response definitions)
#    CR       : Complete Remission — blasts < 5%, ANC ≥ 1.0, PLT ≥ 100
#    CRi      : CR with incomplete hematologic recovery (ANC < 1.0 OR PLT < 100)
#    CRh      : CR with partial hematologic recovery (ANC ≥ 0.5 AND PLT ≥ 50)
#    MLFS     : Morphologic Leukemia-Free State (blasts < 5%, no count recovery req)
#    PR       : Partial Remission (blasts 5-25%, ≥50% decrease)
#    PD       : Progressive Disease
#    NR       : No Response / Refractory
#    MRD_neg  : MRD-negative (TRUE/FALSE) — PCR or MFC based
#    blast_pct: % blasts at assessment (for waterfall plot)
#    Patient_ID: unique patient identifier
# ---------------------------------------------------------------------------

required_cols <- c("Patient_ID")
missing_req   <- setdiff(required_cols, names(df))
if (length(missing_req) > 0) {
  stop("Missing required columns: ", paste(missing_req, collapse = ", "))
}

# Helper: safely pull column or return NA vector
pull_col <- function(data, col, default = NA) {
  if (col %in% names(data)) data[[col]] else rep(default, nrow(data))
}

# ---------------------------------------------------------------------------
# 3. Construct composite response categories
# ---------------------------------------------------------------------------
# If individual response columns are missing, derive from Best_Response
if (!"CR" %in% names(df) & "Best_Response" %in% names(df)) {
  cat("Deriving response columns from Best_Response...\n")
  br <- tolower(as.character(df$Best_Response))
  df$CR   <- br %in% c("cr", "cr mrd-neg", "2", "2.0")
  df$CRi  <- br %in% c("cri", "4", "4.0")
  df$CRh  <- br %in% c("crh", "3", "3.0")
  df$CRm  <- br %in% c("crm", "7", "7.0")
  df$MLFS <- br %in% c("mlfs", "1", "1.0")
  df$PR   <- br %in% c("pr", "8", "8.0")
  df$PD   <- br %in% c("treatment failure", "9", "9.0")
  df$NR   <- br %in% c("nr", "no response", "refractory")
}

cr_col   <- pull_col(df, "CR",   FALSE)
cri_col  <- pull_col(df, "CRi",  FALSE)
crh_col  <- pull_col(df, "CRh",  FALSE)
mlfs_col <- pull_col(df, "MLFS", FALSE)
pr_col   <- pull_col(df, "PR",   FALSE)
pd_col   <- pull_col(df, "PD",   FALSE)
nr_col   <- pull_col(df, "NR",   FALSE)
mrd_col  <- pull_col(df, "MRD_neg", NA)

# Logical coercion (handle 1/0, TRUE/FALSE, "Yes"/"No", SPSS labels like "CR"/"Non-CR")
to_logical <- function(x) {
  if (is.logical(x)) return(x)
  if (is.numeric(x)) return(x == 1)
  x_lower <- tolower(as.character(x))
  x_lower %in% c("true", "yes", "1", "cr", "cri", "crh", "crm", "mlfs", "pr",
                  "orr", "ccr", "positive", "achieved")
}

cr_col   <- to_logical(cr_col)
cri_col  <- to_logical(cri_col)
crh_col  <- to_logical(crh_col)
mlfs_col <- to_logical(mlfs_col)
pr_col   <- to_logical(pr_col)
pd_col   <- to_logical(pd_col)
nr_col   <- to_logical(nr_col)
mrd_col  <- to_logical(mrd_col)

# Composite cCR = CR + CRi + CRh + MLFS (ELN 2022 composite)
ccr_col <- cr_col | cri_col | crh_col | mlfs_col

# Best response hierarchy label
response_label <- dplyr::case_when(
  cr_col & !is.na(mrd_col) & mrd_col ~ "CR MRD-neg",
  cr_col                              ~ "CR MRD+/unknown",
  crh_col                             ~ "CRh",
  cri_col                             ~ "CRi",
  mlfs_col                            ~ "MLFS",
  pr_col                              ~ "PR",
  pd_col                              ~ "PD",
  nr_col                              ~ "NR",
  TRUE                                ~ "Unknown"
)

df$Response_Category <- response_label
df$cCR               <- ccr_col
df$MRD_neg           <- mrd_col

# ---------------------------------------------------------------------------
# 4. Summary table: response rates with 95% CI (Wilson score)
# ---------------------------------------------------------------------------
wilson_ci <- function(k, n, conf = 0.95) {
  if (n == 0) return(c(NA, NA))
  z   <- qnorm(1 - (1 - conf) / 2)
  p   <- k / n
  lo  <- (p + z^2/(2*n) - z * sqrt(p*(1-p)/n + z^2/(4*n^2))) / (1 + z^2/n)
  hi  <- (p + z^2/(2*n) + z * sqrt(p*(1-p)/n + z^2/(4*n^2))) / (1 + z^2/n)
  round(c(lo, hi) * 100, 1)
}

n_total <- nrow(df)

build_row <- function(label, flag_vec) {
  k    <- sum(flag_vec, na.rm = TRUE)
  pct  <- round(k / n_total * 100, 1)
  ci   <- wilson_ci(k, n_total)
  data.frame(
    Response       = label,
    N              = k,
    Percent        = pct,
    CI_95_low      = ci[1],
    CI_95_high     = ci[2],
    stringsAsFactors = FALSE
  )
}

summary_df <- rbind(
  build_row("cCR (CR+CRi+CRh+MLFS)", ccr_col),
  build_row("CR",                     cr_col),
  build_row("CR MRD-negative",        cr_col & !is.na(mrd_col) & mrd_col),
  build_row("CRh",                    crh_col),
  build_row("CRi",                    cri_col),
  build_row("MLFS",                   mlfs_col),
  build_row("PR",                     pr_col),
  build_row("PD/NR",                  pd_col | nr_col)
)
summary_df$`Rate (95% CI)` <- paste0(
  summary_df$Percent, "% (",
  summary_df$CI_95_low, "–", summary_df$CI_95_high, "%)"
)

cat("\n--- AML Composite Response Summary (Cycle", cycle_label, ") ---\n")
print(summary_df[, c("Response", "N", "Rate (95% CI)")])

# ---------------------------------------------------------------------------
# 5. Export .docx table
# ---------------------------------------------------------------------------
ft_data <- summary_df[, c("Response", "N", "Percent", "CI_95_low", "CI_95_high")]
names(ft_data) <- c("Response Category", "N", "%", "95% CI Low", "95% CI High")

ft <- flextable(ft_data) |>
  set_caption(paste0("AML Composite Response Rates — Assessment Cycle ", cycle_label,
                     " (N=", n_total, ")")) |>
  bold(i = 1, bold = TRUE) |>   # bold the cCR row
  bg(i = 1, bg = "#D6EAF8") |>  # highlight cCR row
  autofit() |>
  theme_booktabs()

doc <- read_docx() |>
  body_add_par(paste0("AML Composite Response Analysis — Cycle ", cycle_label), style = "heading 1") |>
  body_add_par(paste0("Total patients: N = ", n_total), style = "Normal") |>
  body_add_flextable(ft)

docx_path <- file.path(tables_dir, paste0("AML_Composite_Response_Cycle", cycle_label, ".docx"))
print(doc, target = docx_path)
cat("Table saved to:", docx_path, "\n")

# ---------------------------------------------------------------------------
# 6. Color map for response categories (used by both waterfall and bar plots)
# ---------------------------------------------------------------------------
color_map <- c(
  "CR MRD-neg"     = "#1A5276",
  "CR MRD+/unknown"= "#2E86C1",
  "CRh"            = "#5DADE2",
  "CRi"            = "#85C1E9",
  "MLFS"           = "#AED6F1",
  "PR"             = "#F7DC6F",
  "PD"             = "#E74C3C",
  "NR"             = "#C0392B",
  "Unknown"        = "#BDC3C7"
)

# ---------------------------------------------------------------------------
# 7. Waterfall plot (% blast change from baseline, if available)
# ---------------------------------------------------------------------------
if ("blast_pct_baseline" %in% names(df) && "blast_pct_assessment" %in% names(df)) {
  df$blast_change_pct <- (df$blast_pct_assessment - df$blast_pct_baseline) /
    df$blast_pct_baseline * 100

  plot_df <- df[!is.na(df$blast_change_pct), ] |>
    arrange(blast_change_pct)

  plot_df$Patient_rank <- seq_len(nrow(plot_df))

  p_waterfall <- ggplot(plot_df, aes(x = reorder(Patient_ID, blast_change_pct),
                                     y = blast_change_pct,
                                     fill = Response_Category)) +
    geom_col(width = 0.8) +
    geom_hline(yintercept = c(-50, 0), linetype = c("dashed", "solid"),
               color = c("grey40", "black"), linewidth = 0.5) +
    scale_fill_manual(values = color_map, name = "Best Response") +
    scale_y_continuous(labels = function(x) paste0(x, "%")) +
    labs(
      title    = paste0("AML Blast Reduction — Cycle ", cycle_label),
      subtitle = paste0("N = ", nrow(plot_df), " patients with baseline & assessment blasts"),
      x        = "Patient (ranked by response)",
      y        = "Change in Blast % from Baseline"
    ) +
    theme_minimal(base_size = 11) +
    theme(
      axis.text.x  = element_blank(),
      axis.ticks.x = element_blank(),
      legend.position = "right"
    )

  eps_path <- file.path(figures_dir, paste0("AML_Waterfall_Cycle", cycle_label, ".eps"))
  ggsave(eps_path, plot = p_waterfall, device = "eps", width = 10, height = 6)
  cat("Waterfall plot saved to:", eps_path, "\n")
} else {
  cat("Columns 'blast_pct_baseline' and/or 'blast_pct_assessment' not found.",
      "Skipping waterfall plot.\n")
}

# ---------------------------------------------------------------------------
# 8. Response distribution bar chart
# ---------------------------------------------------------------------------
resp_counts <- df |>
  group_by(Response_Category) |>
  summarise(N = n(), .groups = "drop") |>
  mutate(
    Pct = round(N / n_total * 100, 1),
    Response_Category = factor(Response_Category,
                               levels = c("CR MRD-neg", "CR MRD+/unknown", "CRh",
                                          "CRi", "MLFS", "PR", "PD", "NR", "Unknown"))
  )

p_bar <- ggplot(resp_counts, aes(x = Response_Category, y = Pct, fill = Response_Category)) +
  geom_col(width = 0.6, show.legend = FALSE) +
  geom_text(aes(label = paste0(N, "\n(", Pct, "%)")), vjust = -0.3, size = 3) +
  scale_fill_manual(values = color_map) +
  labs(
    title = paste0("AML Response Distribution — Cycle ", cycle_label),
    x     = "Response Category",
    y     = "% of Patients"
  ) +
  theme_minimal(base_size = 11) +
  theme(axis.text.x = element_text(angle = 30, hjust = 1))

eps_bar <- file.path(figures_dir, paste0("AML_Response_Bar_Cycle", cycle_label, ".eps"))
ggsave(eps_bar, plot = p_bar, device = "eps", width = 8, height = 6)
cat("Response bar chart saved to:", eps_bar, "\n")

cat("\nAML composite response analysis complete.\n")

# ── Emit stats sidecar ────────────────────────────────────────────────────────
tryCatch({
  get_rate <- function(label) {
    row <- summary_df[summary_df$Response == label, ]
    if (nrow(row) == 0 || is.na(row$Percent[1])) return(NULL)
    list(value = row$Percent[1], unit = "percent",
         ci_lower = row$CI_95_low[1], ci_upper = row$CI_95_high[1])
  }
  write_stats_json(
    key_statistics = list(
      n_total       = n_total,
      ccr_rate      = get_rate("cCR (CR+CRi+CRh+MLFS)"),
      cr_rate       = get_rate("CR"),
      mrd_neg_rate  = get_rate("CR MRD-negative"),
      pr_rate       = get_rate("PR"),
      pd_nr_rate    = get_rate("PD/NR")
    ),
    analysis_notes   = list(
      ci_method  = "Wilson score interval",
      cycle      = cycle_label,
      reference  = "Döhner H et al. Blood 2022 ELN recommendations"
    ),
    disease_specific = list(disease = "AML", endpoint = "composite_response_ELN2022")
  )
}, error = function(e) message("[write_stats_json] Skipped (error): ", e$message))
