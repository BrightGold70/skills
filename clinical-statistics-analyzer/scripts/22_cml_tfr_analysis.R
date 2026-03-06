# Script: CML Treatment-Free Remission (TFR) Analysis
# Purpose: BCR-ABL kinetics, TFR rate, molecular relapse-free survival, milestone assessment
# Reference: Hochhaus A et al. ELN recommendations 2020; Mahon FX et al. Lancet Oncol 2010
# Usage: Rscript 22_cml_tfr_analysis.R <dataset_path> [--tfr-only]
#   dataset_path: CSV/XLSX with BCR-ABL longitudinal + TFR data
#   --tfr-only  : optional flag — skip kinetics plot and only run TFR analysis

library(dplyr)
library(ggplot2)
library(survival)
library(survminer)
library(officer)
library(flextable)
library(readxl)
library(tidyr)

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
  stop("Usage: Rscript 22_cml_tfr_analysis.R <dataset_path> [--tfr-only]")
}

input_data_path <- args[1]
tfr_only        <- "--tfr-only" %in% args

output_dir  <- Sys.getenv("CSA_OUTPUT_DIR", "")
if (output_dir == "") stop("CSA_OUTPUT_DIR not set. Export it first: export CSA_OUTPUT_DIR=/path/to/output")
tables_dir  <- file.path(output_dir, "Tables")
figures_dir <- file.path(output_dir, "Figures")
if (!dir.exists(tables_dir))  dir.create(tables_dir,  recursive = TRUE)
if (!dir.exists(figures_dir)) dir.create(figures_dir, recursive = TRUE)

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
ext <- tolower(tools::file_ext(input_data_path))
if (ext %in% c("xlsx", "xls")) {
  df <- read_excel(input_data_path)
} else {
  df <- read.csv(input_data_path, stringsAsFactors = FALSE)
}

cat("Loaded", nrow(df), "records from", input_data_path, "\n")
cat("Columns:", paste(names(df), collapse = ", "), "\n\n")

# ---------------------------------------------------------------------------
# 2. BCR-ABL kinetics plot (longitudinal % IS)
#    Expected columns: Patient_ID, Time_months, BCR_ABL_IS (% IS), TKI
#    Optional:         TKI_Line (1L/2L/3L)
# ---------------------------------------------------------------------------
if (!tfr_only && all(c("Patient_ID", "Time_months", "BCR_ABL_IS") %in% names(df))) {
  cat("--- BCR-ABL Kinetics Plot ---\n")

  kinetics_df <- df[!is.na(df$BCR_ABL_IS) & !is.na(df$Time_months), ]

  # ELN 2020 milestone thresholds (% IS)
  milestones <- data.frame(
    Time_months = c(3,   6,   12,  18),
    BCR_ABL_IS  = c(10,  1,   0.1, 0.01),
    Label       = c("≤10% (CHR)", "≤1% (CCyR)", "≤0.1% (MMR/MR3)", "≤0.01% (MR4)")
  )

  # Determine color variable
  color_var <- if ("TKI" %in% names(kinetics_df)) "TKI" else NULL

  p_kinetics <- ggplot(kinetics_df, aes(x = Time_months, y = BCR_ABL_IS,
                                        group = Patient_ID,
                                        color = if (!is.null(color_var)) .data[[color_var]] else NULL)) +
    geom_line(alpha = 0.4, linewidth = 0.5) +
    geom_point(alpha = 0.6, size = 1.5) +
    # Median smoothed line
    stat_summary(aes(group = if (!is.null(color_var)) .data[[color_var]] else 1),
                 fun = median, geom = "line", linewidth = 1.2, linetype = "solid") +
    # Milestone threshold lines
    geom_hline(data = milestones, aes(yintercept = BCR_ABL_IS),
               linetype = "dashed", color = "grey50", linewidth = 0.4) +
    geom_text(data = milestones,
              aes(x = max(kinetics_df$Time_months, na.rm = TRUE) * 0.95,
                  y = BCR_ABL_IS * 1.5,
                  label = Label),
              inherit.aes = FALSE, hjust = 1, size = 2.8, color = "grey40") +
    # ELN milestone timepoints
    geom_vline(xintercept = c(3, 6, 12, 18), linetype = "dotted",
               color = "grey70", linewidth = 0.4) +
    scale_y_log10(
      breaks = c(100, 10, 1, 0.1, 0.01, 0.001),
      labels = c("100%", "10%", "1%", "0.1%", "0.01%", "0.001%"),
      name   = "BCR-ABL (% IS, log10 scale)"
    ) +
    scale_x_continuous(
      breaks = c(0, 3, 6, 12, 18, 24, 36, 48, 60),
      name   = "Time from TKI initiation (months)"
    ) +
    labs(
      title    = "BCR-ABL Kinetics — Individual Patient Trajectories",
      subtitle = "Dashed lines: ELN 2020 milestone thresholds; solid line: cohort median",
      color    = if (!is.null(color_var)) color_var else NULL
    ) +
    theme_minimal(base_size = 11) +
    theme(legend.position = "right")

  eps_kinetics <- file.path(figures_dir, "CML_BCR_ABL_Kinetics.eps")
  ggsave(eps_kinetics, plot = p_kinetics, device = "eps", width = 10, height = 7)
  cat("BCR-ABL kinetics plot saved to:", eps_kinetics, "\n")

  # ---------------------------------------------------------------------------
  # 2b. ELN Milestone Achievement Table
  #     For each patient, determine if milestone was met at each timepoint
  # ---------------------------------------------------------------------------
  # Summarize: % patients meeting milestone at each ELN timepoint
  milestone_summary <- lapply(
    list(list(t = 3, thresh = 10, label = "3 months: BCR-ABL ≤10%"),
         list(t = 6, thresh = 1,  label = "6 months: BCR-ABL ≤1% (CCyR)"),
         list(t = 12, thresh = 0.1, label = "12 months: BCR-ABL ≤0.1% (MMR)"),
         list(t = 18, thresh = 0.01, label = "18 months: BCR-ABL ≤0.01% (MR4)")),
    function(m) {
      # Per-patient: closest assessment within ±1 month of milestone timepoint
      near <- kinetics_df |>
        filter(abs(Time_months - m$t) <= 1.5) |>
        group_by(Patient_ID) |>
        slice_min(abs(Time_months - m$t), n = 1) |>
        ungroup()

      n_eval <- n_distinct(near$Patient_ID)
      n_met  <- sum(near$BCR_ABL_IS <= m$thresh, na.rm = TRUE)
      pct    <- if (n_eval > 0) round(n_met / n_eval * 100, 1) else NA

      data.frame(
        Milestone     = m$label,
        N_Evaluable   = n_eval,
        N_Met         = n_met,
        Pct_Met       = pct,
        stringsAsFactors = FALSE
      )
    }
  ) |> bind_rows()

  cat("\n--- ELN Milestone Achievements ---\n")
  print(milestone_summary)

  ft_mile <- flextable(milestone_summary) |>
    set_caption("CML ELN 2020 Milestone Achievement Rates") |>
    colformat_num(j = "Pct_Met", suffix = "%") |>
    autofit() |>
    theme_booktabs()

  doc_mile <- read_docx() |>
    body_add_par("CML ELN Milestone Assessment", style = "heading 1") |>
    body_add_flextable(ft_mile)

  docx_mile <- file.path(tables_dir, "CML_ELN_Milestone_Assessment.docx")
  print(doc_mile, target = docx_mile)
  cat("Milestone table saved to:", docx_mile, "\n")
}

# ---------------------------------------------------------------------------
# 3. TFR Analysis
#    Required columns for TFR:
#      Patient_ID, tfr_time (months since TKI stop), tfr_event (1=relapse, 0=censored)
#      Optional: TKI (which TKI was stopped), DMR_duration_months (duration of deep MR before stop),
#                TKI_Line
# ---------------------------------------------------------------------------
tfr_cols_required <- c("Patient_ID", "tfr_time", "tfr_event")
if (!all(tfr_cols_required %in% names(df))) {
  cat("\nTFR columns not found (need: tfr_time, tfr_event). Skipping TFR section.\n")
  cat("TFR analysis complete.\n")
  quit(save = "no")
}

cat("\n--- TFR Analysis ---\n")
tfr_df <- df[!is.na(df$tfr_time) & !is.na(df$tfr_event), ]
cat("N patients in TFR analysis:", nrow(tfr_df), "\n")

# ---------------------------------------------------------------------------
# 3a. TFR Rate (Kaplan-Meier of molecular relapse-free survival)
#     Event = molecular relapse (BCR-ABL detectable above threshold, typically ≥0.1% IS)
# ---------------------------------------------------------------------------
if ("TKI" %in% names(tfr_df)) {
  fit_tfr <- survfit(Surv(tfr_time, tfr_event) ~ TKI, data = tfr_df)
  color_var_tfr <- "TKI"
} else {
  fit_tfr <- survfit(Surv(tfr_time, tfr_event) ~ 1, data = tfr_df)
  color_var_tfr <- NULL
}

# Print 12- and 24-month TFR rates
cat("\nTFR Summary:\n")
print(summary(fit_tfr, times = c(12, 24, 36)))

p_tfr <- ggsurvplot(
  fit_tfr,
  data          = tfr_df,
  pval          = if (!is.null(color_var_tfr)) TRUE else FALSE,
  conf.int      = TRUE,
  risk.table    = TRUE,
  risk.table.col= "strata",
  ggtheme       = theme_minimal(base_size = 11),
  palette       = c("#2E86C1", "#E74C3C", "#27AE60", "#8E44AD"),
  xlab          = "Time from TKI Discontinuation (months)",
  ylab          = "Treatment-Free Remission Probability",
  title         = "Treatment-Free Remission (TFR) — Molecular Relapse-Free Survival",
  break.time.by = 6,
  xlim          = c(0, max(tfr_df$tfr_time, na.rm = TRUE) + 3)
)

eps_tfr <- file.path(figures_dir, "CML_TFR_KaplanMeier.eps")
ggsave(filename = eps_tfr, print(p_tfr), device = "eps", width = 10, height = 8)
cat("TFR KM plot saved to:", eps_tfr, "\n")

# ---------------------------------------------------------------------------
# 3b. Predictors of TFR: Cox model with DMR duration if available
# ---------------------------------------------------------------------------
covariates <- c("TKI", "TKI_Line", "DMR_duration_months", "Age", "Sokal_Score_cat")
available  <- covariates[covariates %in% names(tfr_df)]

if (length(available) > 0) {
  cox_formula <- as.formula(
    paste("Surv(tfr_time, tfr_event) ~", paste(available, collapse = " + "))
  )
  tfr_cox <- coxph(cox_formula, data = tfr_df)
  cat("\n--- Cox Predictors of TFR Loss (Molecular Relapse) ---\n")
  print(summary(tfr_cox))

  # PH assumption test
  cat("\n--- Schoenfeld Residuals Test (PH assumption) ---\n")
  tryCatch({
    zph <- cox.zph(tfr_cox)
    print(zph)
    if (any(zph$table[, "p"] < 0.05, na.rm = TRUE)) {
      warning("PH assumption violated for one or more covariates in TFR Cox model. ",
              "Consider time-stratified or time-varying Cox approach.")
    }
  }, error = function(e) {
    cat("Could not run cox.zph():", conditionMessage(e), "\n")
  })

  library(broom)
  cox_tidy <- tidy(tfr_cox, conf.int = TRUE, exponentiate = TRUE)

  ft_cox <- flextable(cox_tidy[, c("term", "estimate", "conf.low", "conf.high", "p.value")]) |>
    set_header_labels(
      term      = "Covariate",
      estimate  = "HR",
      conf.low  = "95% CI Low",
      conf.high = "95% CI High",
      p.value   = "p-value"
    ) |>
    colformat_num(j = c("estimate", "conf.low", "conf.high"), digits = 2) |>
    colformat_num(j = "p.value", digits = 3) |>
    set_caption("Cox Model: Predictors of TFR Loss") |>
    autofit() |>
    theme_booktabs()

  doc_cox <- read_docx() |>
    body_add_par("CML TFR Cox Model", style = "heading 1") |>
    body_add_flextable(ft_cox)

  print(doc_cox, target = file.path(tables_dir, "CML_TFR_Cox_Model.docx"))
  cat("TFR Cox model saved.\n")
}

# ---------------------------------------------------------------------------
# 3c. TFR rate summary table (12, 24, 36 month rates)
# ---------------------------------------------------------------------------
tfr_summary_rows <- lapply(c(12, 24, 36), function(t) {
  s <- summary(fit_tfr, times = t)
  if (is.null(color_var_tfr)) {
    data.frame(
      Timepoint = paste0(t, " months"),
      Strata    = "All",
      TFR_Rate  = round(s$surv * 100, 1),
      CI_Low    = round(s$lower * 100, 1),
      CI_High   = round(s$upper * 100, 1),
      stringsAsFactors = FALSE
    )
  } else {
    data.frame(
      Timepoint = paste0(t, " months"),
      Strata    = as.character(s$strata),
      TFR_Rate  = round(s$surv * 100, 1),
      CI_Low    = round(s$lower * 100, 1),
      CI_High   = round(s$upper * 100, 1),
      stringsAsFactors = FALSE
    )
  }
}) |> bind_rows()

cat("\n--- TFR Rates at 12/24/36 months ---\n")
print(tfr_summary_rows)

ft_rates <- flextable(tfr_summary_rows) |>
  set_caption("CML Treatment-Free Remission Rates") |>
  autofit() |>
  theme_booktabs()

doc_rates <- read_docx() |>
  body_add_par("CML TFR Summary", style = "heading 1") |>
  body_add_par(paste0("N = ", nrow(tfr_df), " patients who discontinued TKI"), style = "Normal") |>
  body_add_flextable(ft_rates)

print(doc_rates, target = file.path(tables_dir, "CML_TFR_Summary.docx"))
cat("TFR summary table saved to:", file.path(tables_dir, "CML_TFR_Summary.docx"), "\n")

cat("\nCML TFR analysis complete.\n")

# ── Emit stats sidecar ────────────────────────────────────────────────────────
tryCatch({
  stats_list <- list(n_total = nrow(df))
  # TFR rates from tfr_summary_rows if available
  if (exists("tfr_summary_rows") && is.data.frame(tfr_summary_rows)) {
    get_tfr <- function(mo) {
      row <- tfr_summary_rows[tfr_summary_rows$Timepoint == paste0(mo, " months") &
                              tfr_summary_rows$Strata == "All", ]
      if (nrow(row) == 0) return(NULL)
      list(value = row$TFR_Rate[1], unit = "percent",
           ci_lower = row$CI_Low[1], ci_upper = row$CI_High[1])
    }
    stats_list$tfr_12mo <- get_tfr(12)
    stats_list$tfr_24mo <- get_tfr(24)
    stats_list$tfr_36mo <- get_tfr(36)
  }
  # ELN milestone rates if available
  if (exists("milestone_summary") && is.data.frame(milestone_summary)) {
    get_ms <- function(label) {
      row <- milestone_summary[grepl(label, milestone_summary$Milestone, fixed = TRUE), ]
      if (nrow(row) == 0 || is.na(row$Pct_Met[1])) return(NULL)
      list(value = row$Pct_Met[1], unit = "percent", n_evaluable = row$N_Evaluable[1])
    }
    stats_list$mmr_12mo  <- get_ms("12 months")
    stats_list$mr4_18mo  <- get_ms("18 months")
  }
  write_stats_json(
    key_statistics   = stats_list,
    analysis_notes   = list(reference = "Hochhaus A et al. ELN recommendations 2020"),
    disease_specific = list(disease = "CML", endpoint = "TFR_ELN2020")
  )
}, error = function(e) message("[write_stats_json] Skipped (error): ", e$message))
