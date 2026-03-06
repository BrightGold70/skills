# Script: HCT GVHD and Transplant Outcomes Analysis
# Purpose: aGVHD/cGVHD cumulative incidence (competing risks), engraftment kinetics,
#          NRM, relapse CI, and GRFS analysis
# Reference: Wolff D et al. BBMT 2011 (NIH cGVHD); Flowers ME et al. Blood 2011;
#            Ruggeri A et al. Leukemia 2016 (GRFS); Schemitsch 2014 (competing risks)
# Usage: Rscript 24_hct_gvhd_analysis.R <dataset_path> [--no-engraftment]

library(survival)
library(cmprsk)
library(dplyr)
library(ggplot2)
library(officer)
library(flextable)
library(readxl)
library(tidyr)
library(survminer)

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
  stop("Usage: Rscript 24_hct_gvhd_analysis.R <dataset_path> [--no-engraftment]")
}

input_data_path  <- args[1]
skip_engraftment <- "--no-engraftment" %in% args

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
df  <- if (ext %in% c("xlsx", "xls")) read_excel(input_data_path) else
         read.csv(input_data_path, stringsAsFactors = FALSE)

cat("Loaded", nrow(df), "patients\n")

# Helper: safe column extraction
pull_col <- function(data, col, default = NA) {
  if (col %in% names(data)) data[[col]] else rep(default, nrow(data))
}

# ---------------------------------------------------------------------------
# 2. Cumulative Incidence Function helper
#    Uses cmprsk::cuminc; produces ggplot-compatible data frame
# ---------------------------------------------------------------------------
ci_to_df <- function(ci_obj, groups = NULL) {
  # Extract CI estimates from cuminc object
  out <- lapply(names(ci_obj)[!names(ci_obj) %in% "Tests"], function(nm) {
    data.frame(
      time  = ci_obj[[nm]]$time,
      est   = ci_obj[[nm]]$est,
      var   = ci_obj[[nm]]$var,
      group = nm,
      stringsAsFactors = FALSE
    )
  })
  bind_rows(out)
}

# ---------------------------------------------------------------------------
# 3. aGVHD Cumulative Incidence (competing event = death without aGVHD)
#    Expected columns:
#      time_agvhd      : days from HCT to aGVHD onset or last follow-up
#      agvhd_status    : 0=censored, 1=aGVHD (grade II-IV), 2=death without aGVHD
#      agvhd_grade     : I/II/III/IV (optional, for grade III-IV analysis)
#      group_var       : stratification variable (optional — donor type, conditioning, etc.)
# ---------------------------------------------------------------------------
cat("\n--- 3a. Acute GVHD Cumulative Incidence ---\n")

agvhd_time   <- pull_col(df, "time_agvhd")
agvhd_status <- pull_col(df, "agvhd_status")  # 0=censor, 1=aGVHD II-IV, 2=death
group_var    <- if ("Donor_Type" %in% names(df)) df$Donor_Type else
                if ("Conditioning" %in% names(df)) df$Conditioning else NULL

if (!all(is.na(agvhd_time)) && !all(is.na(agvhd_status))) {
  valid_agvhd <- !is.na(agvhd_time) & !is.na(agvhd_status)

  if (!is.null(group_var) && !all(is.na(group_var))) {
    ci_agvhd <- cuminc(
      ftime   = agvhd_time[valid_agvhd],
      fstatus = agvhd_status[valid_agvhd],
      group   = group_var[valid_agvhd]
    )
  } else {
    ci_agvhd <- cuminc(
      ftime   = agvhd_time[valid_agvhd],
      fstatus = agvhd_status[valid_agvhd]
    )
  }

  # Extract D+100 cumulative incidence of aGVHD (event=1)
  cat("aGVHD CI object names:", paste(names(ci_agvhd)[names(ci_agvhd) != "Tests"], collapse=", "), "\n")
  if ("Tests" %in% names(ci_agvhd)) {
    cat("Gray's test p-value:", round(ci_agvhd$Tests[1, "p"], 4), "\n")
  }

  ci_agvhd_df <- ci_to_df(ci_agvhd) |>
    filter(grepl(" 1$| 1 ", group) | group == "1")  # keep event=1 rows

  # Plot
  p_agvhd <- ggplot(ci_agvhd_df, aes(x = time, y = est, color = group)) +
    geom_step(linewidth = 0.9) +
    geom_ribbon(aes(ymin = est - 1.96 * sqrt(var),
                    ymax = est + 1.96 * sqrt(var),
                    fill = group), alpha = 0.15, color = NA) +
    geom_vline(xintercept = 100, linetype = "dashed", color = "grey50") +
    annotate("text", x = 103, y = 0.02, label = "D+100", size = 3, color = "grey40", hjust = 0) +
    scale_y_continuous(labels = scales::percent_format(), limits = c(0, 1),
                       name = "Cumulative Incidence") +
    scale_x_continuous(name = "Days from HCT") +
    labs(
      title    = "Cumulative Incidence of Grade II-IV Acute GVHD",
      subtitle = "Competing event: death without aGVHD",
      color    = "Group", fill = "Group"
    ) +
    theme_minimal(base_size = 11) +
    theme(legend.position = "right")

  eps_agvhd <- file.path(figures_dir, "HCT_aGVHD_CumulativeIncidence.eps")
  ggsave(eps_agvhd, plot = p_agvhd, device = "eps", width = 9, height = 6)
  cat("aGVHD CI plot saved to:", eps_agvhd, "\n")

  # Grade III-IV aGVHD if column available
  if ("agvhd_status34" %in% names(df)) {
    agvhd34_status <- df$agvhd_status34[valid_agvhd]
    ci_agvhd34 <- cuminc(
      ftime   = agvhd_time[valid_agvhd],
      fstatus = agvhd34_status,
      group   = if (!is.null(group_var)) group_var[valid_agvhd] else rep("All", sum(valid_agvhd))
    )
    cat("Grade III-IV aGVHD CI computed.\n")
  }
} else {
  cat("aGVHD columns (time_agvhd, agvhd_status) not found. Skipping.\n")
}

# ---------------------------------------------------------------------------
# 4. Chronic GVHD Cumulative Incidence (NIH 2014 criteria)
#    Expected columns:
#      time_cgvhd      : days to cGVHD onset or last follow-up
#      cgvhd_status    : 0=censor, 1=cGVHD (any), 2=death without cGVHD
#      cgvhd_severity  : Mild/Moderate/Severe (NIH) — optional
# ---------------------------------------------------------------------------
cat("\n--- 4a. Chronic GVHD Cumulative Incidence (NIH 2014) ---\n")

cgvhd_time   <- pull_col(df, "time_cgvhd")
cgvhd_status <- pull_col(df, "cgvhd_status")   # 0=censor, 1=any cGVHD, 2=death

if (!all(is.na(cgvhd_time)) && !all(is.na(cgvhd_status))) {
  valid_cgvhd <- !is.na(cgvhd_time) & !is.na(cgvhd_status)

  ci_cgvhd <- cuminc(
    ftime   = cgvhd_time[valid_cgvhd],
    fstatus = cgvhd_status[valid_cgvhd],
    group   = if (!is.null(group_var)) group_var[valid_cgvhd] else rep("All", sum(valid_cgvhd))
  )

  cat("cGVHD CI computed.\n")
  if ("Tests" %in% names(ci_cgvhd)) {
    cat("Gray's test p-value:", round(ci_cgvhd$Tests[1, "p"], 4), "\n")
  }

  ci_cgvhd_df <- ci_to_df(ci_cgvhd) |>
    filter(grepl(" 1$| 1 ", group) | group == "1")

  p_cgvhd <- ggplot(ci_cgvhd_df, aes(x = time / 30.44, y = est, color = group)) +
    geom_step(linewidth = 0.9) +
    geom_ribbon(aes(ymin = est - 1.96 * sqrt(var),
                    ymax = est + 1.96 * sqrt(var),
                    fill = group), alpha = 0.15, color = NA) +
    geom_vline(xintercept = c(6, 12), linetype = "dashed", color = "grey50") +
    annotate("text", x = c(6.2, 12.2), y = 0.02, label = c("6m", "12m"),
             size = 3, color = "grey40", hjust = 0) +
    scale_y_continuous(labels = scales::percent_format(), limits = c(0, 1),
                       name = "Cumulative Incidence") +
    scale_x_continuous(name = "Months from HCT") +
    labs(
      title    = "Cumulative Incidence of Chronic GVHD (NIH 2014)",
      subtitle = "Competing event: death without cGVHD",
      color    = "Group", fill = "Group"
    ) +
    theme_minimal(base_size = 11) +
    theme(legend.position = "right")

  eps_cgvhd <- file.path(figures_dir, "HCT_cGVHD_CumulativeIncidence.eps")
  ggsave(eps_cgvhd, plot = p_cgvhd, device = "eps", width = 9, height = 6)
  cat("cGVHD CI plot saved to:", eps_cgvhd, "\n")

  # Severity breakdown table
  if ("cgvhd_severity" %in% names(df)) {
    sev_tab <- df |>
      filter(!is.na(cgvhd_severity)) |>
      count(cgvhd_severity) |>
      mutate(Pct = round(n / sum(n) * 100, 1))

    cat("\ncGVHD Severity Distribution (NIH):\n")
    print(sev_tab)

    ft_sev <- flextable(sev_tab) |>
      set_header_labels(cgvhd_severity = "NIH Severity", n = "N", Pct = "%") |>
      set_caption("Chronic GVHD Severity Distribution (NIH 2014 Criteria)") |>
      autofit() |>
      theme_booktabs()

    doc_sev <- read_docx() |>
      body_add_par("HCT: Chronic GVHD Severity", style = "heading 1") |>
      body_add_flextable(ft_sev)

    print(doc_sev, target = file.path(tables_dir, "HCT_cGVHD_Severity.docx"))
    cat("cGVHD severity table saved.\n")
  }
} else {
  cat("cGVHD columns (time_cgvhd, cgvhd_status) not found. Skipping.\n")
}

# ---------------------------------------------------------------------------
# 5. GRFS — Graft-versus-Host/Relapse-Free Survival (competing risks)
#    GRFS event = composite: grade III-IV aGVHD, moderate-severe cGVHD,
#                             relapse, or death from any cause
#    This is a COMPOSITE endpoint analyzed via competing risks (Fine-Gray)
#    for specific components, or as a simple event-free survival endpoint.
#    Expected columns:
#      grfs_time   : days to first GRFS event or censoring
#      grfs_event  : 0=GRFS event-free (censored), 1=GRFS event occurred
#      grfs_competing: 0=censor, 1=GRFS event, 2=death without GRFS event (if separable)
# ---------------------------------------------------------------------------
cat("\n--- 5. GRFS Analysis (Graft-vs-Host/Relapse-Free Survival) ---\n")

grfs_time       <- pull_col(df, "grfs_time")
grfs_event      <- pull_col(df, "grfs_event")
grfs_competing  <- pull_col(df, "grfs_competing")  # may be NA if not separated

if (!all(is.na(grfs_time)) && !all(is.na(grfs_event))) {
  valid_grfs <- !is.na(grfs_time) & !is.na(grfs_event)
  cat("N patients with GRFS data:", sum(valid_grfs), "\n")

  # If grfs_competing is available, use Fine-Gray; else use KM (GRFS as simple event)
  if (!all(is.na(grfs_competing))) {
    cat("Using Fine-Gray competing risks for GRFS (competing events separated).\n")

    ci_grfs <- cuminc(
      ftime   = grfs_time[valid_grfs],
      fstatus = grfs_competing[valid_grfs],
      group   = if (!is.null(group_var)) group_var[valid_grfs] else rep("All", sum(valid_grfs))
    )

    cat("Gray's test:\n")
    if ("Tests" %in% names(ci_grfs)) print(ci_grfs$Tests)

    ci_grfs_df <- ci_to_df(ci_grfs) |>
      filter(grepl(" 1$| 1 ", group) | group == "1")

    p_grfs <- ggplot(ci_grfs_df, aes(x = time / 30.44, y = est, color = group)) +
      geom_step(linewidth = 1.0) +
      geom_ribbon(aes(ymin = est - 1.96 * sqrt(var),
                      ymax = est + 1.96 * sqrt(var),
                      fill = group), alpha = 0.15, color = NA) +
      scale_y_continuous(labels = scales::percent_format(), limits = c(0, 1),
                         name = "Cumulative Incidence of GRFS Event") +
      scale_x_continuous(name = "Months from HCT",
                         breaks = seq(0, 60, by = 6)) +
      labs(
        title    = "GRFS — Graft-versus-Host/Relapse-Free Survival",
        subtitle = "Competing risks approach (Fine-Gray); event = aGVHD ≥gr3, cGVHD mod-sev, relapse, death",
        color    = "Group", fill = "Group"
      ) +
      theme_minimal(base_size = 11) +
      theme(legend.position = "right")

    eps_grfs_cr <- file.path(figures_dir, "HCT_GRFS_CumulativeIncidence.eps")
    ggsave(eps_grfs_cr, plot = p_grfs, device = "eps", width = 10, height = 7)
    cat("GRFS cumulative incidence plot saved to:", eps_grfs_cr, "\n")

  } else {
    cat("grfs_competing not found. Analyzing GRFS as event-free survival (KM).\n")

    fit_grfs <- if (!is.null(group_var)) {
      survfit(Surv(grfs_time, grfs_event) ~ group_var, data = df[valid_grfs, ])
    } else {
      survfit(Surv(grfs_time, grfs_event) ~ 1, data = df[valid_grfs, ])
    }

    print(summary(fit_grfs, times = c(180, 365, 730)))  # D+180, 1yr, 2yr

    p_grfs_km <- ggsurvplot(
      fit_grfs,
      data       = df[valid_grfs, ],
      pval       = !is.null(group_var),
      conf.int   = TRUE,
      risk.table = TRUE,
      ggtheme    = theme_minimal(base_size = 11),
      xlab       = "Days from HCT",
      ylab       = "GRFS Probability",
      title      = "GRFS — Kaplan-Meier (no competing risks separation)",
      fun        = "event"
    )

    eps_grfs_km <- file.path(figures_dir, "HCT_GRFS_KaplanMeier.eps")
    ggsave(filename = eps_grfs_km, print(p_grfs_km), device = "eps", width = 10, height = 8)
    cat("GRFS KM plot saved to:", eps_grfs_km, "\n")
  }
} else {
  cat("GRFS columns (grfs_time, grfs_event) not found. Skipping.\n")
}

# ---------------------------------------------------------------------------
# 6. Engraftment kinetics (if not skipped)
#    Expected columns: Patient_ID, anc_engraft_day (ANC ≥500), plt_engraft_day (PLT ≥20k)
#                       graft_failure (0/1), graft_failure_type ("Primary"/"Secondary")
# ---------------------------------------------------------------------------
if (!skip_engraftment && "anc_engraft_day" %in% names(df)) {
  cat("\n--- 6. Engraftment Kinetics ---\n")

  eng_df <- df[!is.na(df$anc_engraft_day) | pull_col(df, "graft_failure", 0) == 1, ]

  # Median engraftment time
  anc_days <- as.numeric(pull_col(eng_df, "anc_engraft_day"))
  plt_days <- as.numeric(pull_col(eng_df, "plt_engraft_day"))

  cat("ANC engraftment (median days):", median(anc_days, na.rm = TRUE), "\n")
  cat("PLT engraftment (median days):", median(plt_days, na.rm = TRUE), "\n")
  cat("Graft failure N:", sum(pull_col(df, "graft_failure", 0) == 1, na.rm = TRUE), "\n")

  # Distribution plot
  eng_long <- tidyr::pivot_longer(
    data.frame(Patient_ID = eng_df$Patient_ID,
               ANC        = anc_days,
               Platelets  = plt_days),
    cols      = c("ANC", "Platelets"),
    names_to  = "Lineage",
    values_to = "Days"
  ) |> filter(!is.na(Days))

  p_eng <- ggplot(eng_long, aes(x = Days, fill = Lineage)) +
    geom_histogram(binwidth = 2, position = "identity", alpha = 0.6, color = "white") +
    geom_vline(data = eng_long |> group_by(Lineage) |> summarise(med = median(Days, na.rm = TRUE)),
               aes(xintercept = med, color = Lineage), linewidth = 1, linetype = "dashed") +
    scale_fill_manual(values  = c("ANC" = "#2E86C1", "Platelets" = "#E74C3C")) +
    scale_color_manual(values = c("ANC" = "#1A5276", "Platelets" = "#922B21")) +
    labs(
      title    = "Engraftment Kinetics — ANC and Platelet Recovery",
      subtitle = "Dashed line = median; binwidth = 2 days",
      x        = "Days to Engraftment from HCT",
      y        = "Number of Patients"
    ) +
    theme_minimal(base_size = 11)

  eps_eng <- file.path(figures_dir, "HCT_Engraftment_Kinetics.eps")
  ggsave(eps_eng, plot = p_eng, device = "eps", width = 9, height = 6)
  cat("Engraftment kinetics plot saved to:", eps_eng, "\n")
}

# ---------------------------------------------------------------------------
# 7. Summary Table: HCT Outcomes Dashboard
# ---------------------------------------------------------------------------
cat("\n--- 7. HCT Outcomes Summary Table ---\n")

summarize_endpoint <- function(label, n_events, n_total, median_time = NA, ci_str = NA) {
  data.frame(
    Endpoint    = label,
    N_Events    = n_events,
    N_Total     = n_total,
    Rate_Pct    = if (!is.na(n_events) && !is.na(n_total) && n_total > 0)
                    round(n_events / n_total * 100, 1) else NA,
    Median_Time = if (!is.na(median_time)) as.character(median_time) else "N/A",
    Notes       = if (!is.na(ci_str)) ci_str else "",
    stringsAsFactors = FALSE
  )
}

outcomes_table <- bind_rows(
  summarize_endpoint("aGVHD Grade II-IV",
    n_events = if ("agvhd_status" %in% names(df)) sum(df$agvhd_status == 1, na.rm=TRUE) else NA,
    n_total  = nrow(df)),
  summarize_endpoint("aGVHD Grade III-IV",
    n_events = if ("agvhd_status34" %in% names(df)) sum(df$agvhd_status34 == 1, na.rm=TRUE) else NA,
    n_total  = nrow(df)),
  summarize_endpoint("cGVHD (any)",
    n_events = if ("cgvhd_status" %in% names(df)) sum(df$cgvhd_status == 1, na.rm=TRUE) else NA,
    n_total  = nrow(df)),
  summarize_endpoint("cGVHD (mod-severe)",
    n_events = if ("cgvhd_severity" %in% names(df))
                 sum(df$cgvhd_severity %in% c("Moderate","Severe"), na.rm=TRUE) else NA,
    n_total  = nrow(df)),
  summarize_endpoint("Graft Failure",
    n_events = if ("graft_failure" %in% names(df)) sum(df$graft_failure == 1, na.rm=TRUE) else NA,
    n_total  = nrow(df)),
  summarize_endpoint("GRFS Event",
    n_events = if ("grfs_event" %in% names(df)) sum(df$grfs_event == 1, na.rm=TRUE) else NA,
    n_total  = nrow(df))
)

print(outcomes_table)

ft_outcomes <- flextable(outcomes_table) |>
  set_caption(paste0("HCT Transplant Outcomes Summary (N=", nrow(df), ")")) |>
  colformat_num(j = "Rate_Pct", suffix = "%", digits = 1) |>
  autofit() |>
  theme_booktabs()

doc_outcomes <- read_docx() |>
  body_add_par("HCT Transplant Outcomes", style = "heading 1") |>
  body_add_par(paste0("Total patients: N = ", nrow(df)), style = "Normal") |>
  body_add_flextable(ft_outcomes)

docx_out <- file.path(tables_dir, "HCT_Outcomes_Summary.docx")
print(doc_outcomes, target = docx_out)
cat("HCT outcomes summary saved to:", docx_out, "\n")

cat("\nHCT GVHD and transplant outcomes analysis complete.\n")

# ── Emit stats sidecar ────────────────────────────────────────────────────────
tryCatch({
  get_outcome_rate <- function(label) {
    row <- outcomes_table[outcomes_table$Endpoint == label, ]
    if (nrow(row) == 0 || is.na(row$Rate_Pct[1])) return(NULL)
    list(value = row$Rate_Pct[1], unit = "percent", n_events = row$N_Events[1])
  }
  write_stats_json(
    key_statistics = list(
      n_total               = nrow(df),
      agvhd_grade2_4_rate   = get_outcome_rate("aGVHD Grade II-IV"),
      agvhd_grade3_4_rate   = get_outcome_rate("aGVHD Grade III-IV"),
      cgvhd_any_rate        = get_outcome_rate("cGVHD (any)"),
      cgvhd_mod_severe_rate = get_outcome_rate("cGVHD (mod-severe)"),
      graft_failure_rate    = get_outcome_rate("Graft Failure"),
      grfs_event_rate       = get_outcome_rate("GRFS Event")
    ),
    analysis_notes   = list(
      cgvhd_criteria = "NIH 2014",
      grfs_definition = "Grade III-IV aGVHD, moderate-severe cGVHD, relapse, or death"
    ),
    disease_specific = list(disease = "HCT", endpoint = "GVHD_GRFS")
  )
}, error = function(e) message("[write_stats_json] Skipped (error): ", e$message))
