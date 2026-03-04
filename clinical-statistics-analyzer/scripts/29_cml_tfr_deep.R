#!/usr/bin/env Rscript
# 29_cml_tfr_deep.R — Deep TFR analysis
#
# Usage: Rscript 29_cml_tfr_deep.R <dataset>
#
# Outputs:
#   Figures/CML_TFR_Relapse_Kinetics.eps — Spaghetti plot of BCR-ABL post-TFR
#   Figures/CML_TFR_MMR_Loss_KM.eps      — KM curve for time to MMR loss
#   Figures/CML_TFR_MMR_Loss_CI.eps      — Cumulative incidence with competing risks
#   Tables/CML_TFR_Deep_Analysis.docx    — Summary with predictors of MMR loss

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(survival)
  library(survminer)
  library(flextable)
  library(officer)
})

# --- Parse arguments ---
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: Rscript 29_cml_tfr_deep.R <dataset>")
}

dataset_path <- args[1]

output_dir <- Sys.getenv("CSA_OUTPUT_DIR", ".")
tables_dir <- file.path(output_dir, "Tables")
figures_dir <- file.path(output_dir, "Figures")
dir.create(tables_dir, showWarnings = FALSE, recursive = TRUE)
dir.create(figures_dir, showWarnings = FALSE, recursive = TRUE)

# --- Load data ---
df <- read.csv(dataset_path, stringsAsFactors = FALSE)
cat("Loaded", nrow(df), "patients from", dataset_path, "\n")

# --- Filter TFR patients ---
tfr_df <- df %>%
  filter(!is.na(tfr_start_date) & tfr_start_date != "")

cat("Found", nrow(tfr_df), "patients who attempted TFR\n")

if (nrow(tfr_df) < 2) {
  cat("Insufficient TFR patients for analysis — generating summary only\n")

  ft <- flextable(data.frame(
    Metric = c("TFR attempted", "Sustained TFR"),
    N = c(nrow(tfr_df), sum(is.na(tfr_df$mmr_loss_date)))
  )) %>%
    set_caption("TFR Deep Analysis Summary") %>%
    theme_vanilla()

  doc <- read_docx() %>%
    body_add_par("CML TFR Deep Analysis", style = "heading 1") %>%
    body_add_par("Insufficient patients for detailed TFR analysis.") %>%
    body_add_flextable(ft)
  print(doc, target = file.path(tables_dir, "CML_TFR_Deep_Analysis.docx"))

  cat("29_cml_tfr_deep.R completed (insufficient TFR patients)\n")
  quit(save = "no", status = 0)
}

# --- Parse dates ---
tfr_df <- tfr_df %>%
  mutate(
    tfr_start = as.Date(tfr_start_date),
    mmr_loss = as.Date(mmr_loss_date),
    tfr_restart = as.Date(tfr_restart_date),
    # Time to MMR loss (months) — censored at last follow-up or restart
    mmr_loss_event = ifelse(!is.na(mmr_loss), 1, 0),
    # Calculate follow-up time from TFR start
    time_to_event = case_when(
      !is.na(mmr_loss) ~ as.numeric(difftime(mmr_loss, tfr_start, units = "days")) / 30.44,
      !is.na(tfr_restart) ~ as.numeric(difftime(tfr_restart, tfr_start, units = "days")) / 30.44,
      TRUE ~ as.numeric(difftime(Sys.Date(), tfr_start, units = "days")) / 30.44
    )
  ) %>%
  filter(!is.na(time_to_event) & time_to_event > 0)

# --- 1. Molecular relapse kinetics (spaghetti plot) ---
# Gather post-TFR BCR-ABL measurements
bcr_abl_cols <- grep("^bcr_abl_\\d+m$", names(df), value = TRUE)
if (length(bcr_abl_cols) > 0 && nrow(tfr_df) > 0) {
  spaghetti_data <- data.frame()

  for (i in seq_len(nrow(tfr_df))) {
    pid <- tfr_df$Patient_ID[i]
    patient_row <- df[df$Patient_ID == pid, ]

    for (col in bcr_abl_cols) {
      tp <- as.numeric(gsub("bcr_abl_(\\d+)m", "\\1", col))
      val <- patient_row[[col]]
      if (!is.na(val) && val > 0) {
        spaghetti_data <- rbind(spaghetti_data, data.frame(
          Patient_ID = pid,
          Months = tp,
          BCR_ABL = val,
          stringsAsFactors = FALSE
        ))
      }
    }
  }

  if (nrow(spaghetti_data) > 0) {
    p_spaghetti <- ggplot(spaghetti_data,
                          aes(x = Months, y = BCR_ABL, group = Patient_ID, color = Patient_ID)) +
      geom_line(alpha = 0.7, linewidth = 0.8) +
      geom_point(size = 1.5) +
      scale_y_log10(
        labels = scales::comma,
        breaks = c(0.001, 0.01, 0.1, 1, 10, 100)
      ) +
      geom_hline(yintercept = 0.1, linetype = "dashed", color = "red", alpha = 0.5) +
      annotate("text", x = max(spaghetti_data$Months), y = 0.1,
               label = "MMR (0.1%)", hjust = 1, vjust = -0.5, size = 3, color = "red") +
      labs(
        title = "BCR-ABL Kinetics Post-TFR",
        x = "Months from Diagnosis",
        y = "BCR-ABL % IS (log scale)"
      ) +
      theme_minimal(base_size = 12) +
      theme(
        plot.title = element_text(hjust = 0.5, face = "bold"),
        legend.position = "none"
      )

    ggsave(
      file.path(figures_dir, "CML_TFR_Relapse_Kinetics.eps"),
      plot = p_spaghetti, device = "eps", width = 10, height = 6
    )
    cat("Saved: CML_TFR_Relapse_Kinetics.eps\n")
  }
}

# --- 2. KM curve for time to MMR loss ---
if (nrow(tfr_df) >= 2 && sum(tfr_df$mmr_loss_event) > 0) {
  surv_obj <- Surv(tfr_df$time_to_event, tfr_df$mmr_loss_event)
  km_fit <- survfit(surv_obj ~ 1, data = tfr_df)

  p_km <- ggsurvplot(
    km_fit,
    data = tfr_df,
    risk.table = TRUE,
    pval = FALSE,
    conf.int = TRUE,
    title = "Time to Loss of MMR After TFR",
    xlab = "Months from TKI Discontinuation",
    ylab = "Probability of Sustained MMR",
    risk.table.height = 0.25,
    palette = "#2E9FDF",
    ggtheme = theme_minimal(base_size = 12)
  )

  ggsave(
    file.path(figures_dir, "CML_TFR_MMR_Loss_KM.eps"),
    plot = print(p_km), device = "eps", width = 8, height = 7
  )
  cat("Saved: CML_TFR_MMR_Loss_KM.eps\n")
}

# --- 3. Cumulative incidence of MMR loss (competing risk: death) ---
# Use simple CI if cmprsk is available
tryCatch({
  library(cmprsk)

  # Create competing risk status: 0=censored, 1=MMR loss, 2=death without MMR loss
  tfr_df <- tfr_df %>%
    mutate(
      cr_status = case_when(
        mmr_loss_event == 1 ~ 1,
        !is.na(OS_status) & OS_status == 1 ~ 2,
        TRUE ~ 0
      )
    )

  if (length(unique(tfr_df$cr_status[tfr_df$cr_status > 0])) >= 1) {
    ci_fit <- cuminc(tfr_df$time_to_event, tfr_df$cr_status)

    # Plot using base R for EPS compatibility
    eps_path <- file.path(figures_dir, "CML_TFR_MMR_Loss_CI.eps")
    postscript(eps_path, width = 8, height = 6, horizontal = FALSE)
    plot(ci_fit,
         main = "Cumulative Incidence of MMR Loss After TFR",
         xlab = "Months from TKI Discontinuation",
         ylab = "Cumulative Incidence",
         col = c("#D32F2F", "#1976D2"),
         lwd = 2)
    legend("topleft",
           legend = c("MMR Loss", "Death (competing)"),
           col = c("#D32F2F", "#1976D2"),
           lwd = 2, bty = "n")
    dev.off()
    cat("Saved: CML_TFR_MMR_Loss_CI.eps\n")
  }
}, error = function(e) {
  cat("Note: cmprsk-based CI skipped:", conditionMessage(e), "\n")
})

# --- 4. Cox model for predictors of MMR loss ---
predictor_cols <- c("mr4_duration_months", "Treatment")
available_preds <- intersect(predictor_cols, names(tfr_df))

cox_results <- NULL
if (length(available_preds) > 0 && sum(tfr_df$mmr_loss_event) >= 2) {
  formula_str <- paste("Surv(time_to_event, mmr_loss_event) ~",
                       paste(available_preds, collapse = " + "))
  tryCatch({
    cox_fit <- coxph(as.formula(formula_str), data = tfr_df)
    cox_summary <- summary(cox_fit)

    cox_results <- data.frame(
      Variable = rownames(cox_summary$coefficients),
      HR = sprintf("%.2f", cox_summary$coefficients[, "exp(coef)"]),
      `95% CI` = sprintf("%.2f-%.2f",
                         cox_summary$conf.int[, "lower .95"],
                         cox_summary$conf.int[, "upper .95"]),
      `P value` = sprintf("%.3f", cox_summary$coefficients[, "Pr(>|z|)"]),
      check.names = FALSE,
      stringsAsFactors = FALSE
    )
    cat("Cox model fitted with", length(available_preds), "predictors\n")
  }, error = function(e) {
    cat("Note: Cox model skipped:", conditionMessage(e), "\n")
  })
}

# --- Summary table ---
summary_data <- data.frame(
  Metric = c(
    "Total patients",
    "TFR attempted",
    "MMR loss events",
    "Sustained TFR",
    "Median MR4 duration before TFR (months)",
    "Median time to MMR loss (months)"
  ),
  Value = c(
    nrow(df),
    nrow(tfr_df),
    sum(tfr_df$mmr_loss_event),
    sum(tfr_df$mmr_loss_event == 0),
    ifelse("mr4_duration_months" %in% names(tfr_df),
           sprintf("%.1f", median(tfr_df$mr4_duration_months, na.rm = TRUE)),
           "N/A"),
    ifelse(sum(tfr_df$mmr_loss_event) > 0,
           sprintf("%.1f", median(tfr_df$time_to_event[tfr_df$mmr_loss_event == 1])),
           "Not reached")
  ),
  stringsAsFactors = FALSE
)

ft_summary <- flextable(summary_data) %>%
  set_caption("TFR Deep Analysis Summary") %>%
  theme_vanilla() %>%
  autofit()

doc <- read_docx() %>%
  body_add_par("CML TFR Deep Analysis", style = "heading 1") %>%
  body_add_flextable(ft_summary)

# Add Cox results if available
if (!is.null(cox_results)) {
  ft_cox <- flextable(cox_results) %>%
    set_caption("Predictors of MMR Loss (Cox Proportional Hazards)") %>%
    theme_vanilla() %>%
    autofit()

  doc <- doc %>%
    body_add_par("") %>%
    body_add_par("Predictors of MMR Loss", style = "heading 2") %>%
    body_add_flextable(ft_cox)
}

print(doc, target = file.path(tables_dir, "CML_TFR_Deep_Analysis.docx"))
cat("Saved: CML_TFR_Deep_Analysis.docx\n")

cat("29_cml_tfr_deep.R completed successfully\n")
