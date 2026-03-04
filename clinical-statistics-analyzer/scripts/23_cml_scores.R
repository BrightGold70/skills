#!/usr/bin/env Rscript

# 23_cml_scores.R
# Computes Sokal, Hasford, and ELTS scores for Chronic Myeloid Leukemia (CML)
# Generates a comparison table and Kaplan-Meier survival curves.

suppressPackageStartupMessages({
  library(survival)
  library(survminer)
  library(flextable)
  library(officer)
  library(ggplot2)
  library(dplyr)
  library(tidyr)
  library(readxl)
  library(haven)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  stop("Usage: Rscript 23_cml_scores.R <dataset_path>")
}
data_path <- args[1]

# Set up output directories
out_dir <- Sys.getenv("CSA_OUTPUT_DIR", "")
if (out_dir == "") stop("CSA_OUTPUT_DIR not set. Export it first: export CSA_OUTPUT_DIR=/path/to/output")
dir.create(file.path(out_dir, "Tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(out_dir, "Figures"), recursive = TRUE, showWarnings = FALSE)

# Read dataset
ext <- tolower(tools::file_ext(data_path))
if (ext == "csv") {
  df <- read.csv(data_path, stringsAsFactors = FALSE)
} else if (ext %in% c("xls", "xlsx")) {
  df <- read_excel(data_path)
} else if (ext == "rds") {
  df <- readRDS(data_path)
} else if (ext == "sav") {
  df <- read_sav(data_path)
} else {
  stop("Unsupported file format. Please provide .csv, .xlsx, .rds, or .sav.")
}

# Column Mapping
get_col <- function(candidates) {
  m <- intersect(tolower(colnames(df)), tolower(candidates))
  if (length(m) > 0) return(colnames(df)[tolower(colnames(df)) == m[1]][1])
  return(NULL)
}

col_age <- get_col(c("age", "age_yrs", "age_years"))
col_spleen <- get_col(c("spleen_size_cm", "spleen", "spleen_cm", "spleen_palpable"))
col_plt <- get_col(c("platelets", "plt", "platelet"))
col_blasts <- get_col(c("blasts_pb", "blasts", "pb_blasts", "blast"))
col_baso <- get_col(c("basophils", "baso", "basophils_pb"))
col_eos <- get_col(c("eosinophils", "eos", "eosinophils_pb"))
col_os_time <- get_col(c("os_time", "os_months", "os_days", "survival_time", "os"))
col_os_stat <- get_col(c("os_status", "os_event", "status", "death"))

# Sokal Score
# Formula: exp(0.0116*(age - 43.4) + 0.0345*(spleen - 7.51) + 0.188*((platelets/700)^2 - 0.563) + 0.0887*(blasts - 2.10))
# Risk groups: Low < 0.8, Intermediate 0.8-1.2, High > 1.2
if(!is.null(col_age) && !is.null(col_spleen) && !is.null(col_plt) && !is.null(col_blasts)) {
  df$Sokal_Score <- exp(0.0116*(df[[col_age]] - 43.4) +
                        0.0345*(df[[col_spleen]] - 7.51) +
                        0.188*((df[[col_plt]]/700)^2 - 0.563) +
                        0.0887*(df[[col_blasts]] - 2.10))
  df$Sokal_Risk <- NA_character_
  df$Sokal_Risk[df$Sokal_Score < 0.8] <- "Low"
  df$Sokal_Risk[df$Sokal_Score >= 0.8 & df$Sokal_Score <= 1.2] <- "Intermediate"
  df$Sokal_Risk[df$Sokal_Score > 1.2] <- "High"
  df$Sokal_Risk <- factor(df$Sokal_Risk, levels=c("Low", "Intermediate", "High"))
  cat("Sokal score calculated.\n")
} else {
  warning("Missing variables for Sokal score. Required: Age, Spleen, Platelets, Blasts. Skipping.")
}

# Hasford Score
# Formula: (0.666 if age>=50 else 0) + 0.042*spleen + 1.0584*basophils + 0.0584*blasts + 0.20399*(if platelets>1500 then 1 else 0) + 0.0413*eosinophils) * 1000
# Risk groups: Low <= 780, Intermediate 781-1480, High > 1480
if(!is.null(col_age) && !is.null(col_spleen) && !is.null(col_plt) && !is.null(col_blasts) && !is.null(col_baso) && !is.null(col_eos)) {
  df$Hasford_Score <- (ifelse(df[[col_age]] >= 50, 0.666, 0) +
                       0.042 * df[[col_spleen]] +
                       1.0584 * df[[col_baso]] +
                       0.0584 * df[[col_blasts]] +
                       0.20399 * ifelse(df[[col_plt]] > 1500, 1, 0) +
                       0.0413 * df[[col_eos]]) * 1000
  df$Hasford_Risk <- NA_character_
  df$Hasford_Risk[df$Hasford_Score <= 780] <- "Low"
  df$Hasford_Risk[df$Hasford_Score > 780 & df$Hasford_Score <= 1480] <- "Intermediate"
  df$Hasford_Risk[df$Hasford_Score > 1480] <- "High"
  df$Hasford_Risk <- factor(df$Hasford_Risk, levels=c("Low", "Intermediate", "High"))
  cat("Hasford score calculated.\n")
} else {
  warning("Missing variables for Hasford score. Required: Age, Spleen, Basophils, Blasts, Platelets, Eosinophils. Skipping.")
}

# ELTS Score
# Formula: 0.0025*(age/10)^3 + 0.0615*spleen + 0.1052*blasts + 0.4104*log(platelets/1000 + 1)
# Risk groups: Low <= 1.5680, Intermediate 1.5681-2.2185, High > 2.2185
if(!is.null(col_age) && !is.null(col_spleen) && !is.null(col_plt) && !is.null(col_blasts)) {
  df$ELTS_Score <- 0.0025 * (df[[col_age]] / 10)^3 +
                   0.0615 * df[[col_spleen]] +
                   0.1052 * df[[col_blasts]] +
                   0.4104 * log(df[[col_plt]] / 1000 + 1)
  df$ELTS_Risk <- NA_character_
  df$ELTS_Risk[df$ELTS_Score <= 1.5680] <- "Low"
  df$ELTS_Risk[df$ELTS_Score > 1.5680 & df$ELTS_Score <= 2.2185] <- "Intermediate"
  df$ELTS_Risk[df$ELTS_Score > 2.2185] <- "High"
  df$ELTS_Risk <- factor(df$ELTS_Risk, levels=c("Low", "Intermediate", "High"))
  cat("ELTS score calculated.\n")
} else {
  warning("Missing variables for ELTS score. Required: Age, Spleen, Platelets, Blasts. Skipping.")
}

# Generate Summary Table
summary_list <- list()
for(sc in c("Sokal", "Hasford", "ELTS")) {
  risk_col <- paste0(sc, "_Risk")
  if(risk_col %in% colnames(df)) {
    counts <- table(df[[risk_col]], useNA="no")
    pcts <- round(counts / sum(counts) * 100, 1)
    res <- data.frame(
      Score = sc,
      Risk_Group = names(counts),
      N = as.integer(counts),
      Percent = as.numeric(pcts)
    )
    summary_list[[sc]] <- res
  }
}

if(length(summary_list) > 0) {
  summary_df <- bind_rows(summary_list)
  ft_sum <- flextable(summary_df) %>%
    set_caption(caption = "CML Prognostic Scores Summary") %>%
    autofit()
  doc_sum <- read_docx() %>%
    body_add_flextable(value = ft_sum)
  print(doc_sum, target = file.path(out_dir, "Tables", "CML_Scores_Summary.docx"))
  cat("Summary table saved to Tables/CML_Scores_Summary.docx\n")
} else {
  cat("No scores computed, skipping Summary Table.\n")
}

# Generate Concordance Table
conc_list <- list()
if("Sokal_Risk" %in% colnames(df) && "Hasford_Risk" %in% colnames(df)) {
  valid <- !is.na(df$Sokal_Risk) & !is.na(df$Hasford_Risk)
  if(sum(valid) > 0) {
    pct <- round(mean(df$Sokal_Risk[valid] == df$Hasford_Risk[valid]) * 100, 1)
    conc_list[[length(conc_list)+1]] <- data.frame(Comparison = "Sokal vs Hasford", Agreement_Percent = pct, N_Evaluated = sum(valid))
  }
}
if("Sokal_Risk" %in% colnames(df) && "ELTS_Risk" %in% colnames(df)) {
  valid <- !is.na(df$Sokal_Risk) & !is.na(df$ELTS_Risk)
  if(sum(valid) > 0) {
    pct <- round(mean(df$Sokal_Risk[valid] == df$ELTS_Risk[valid]) * 100, 1)
    conc_list[[length(conc_list)+1]] <- data.frame(Comparison = "Sokal vs ELTS", Agreement_Percent = pct, N_Evaluated = sum(valid))
  }
}
if("Hasford_Risk" %in% colnames(df) && "ELTS_Risk" %in% colnames(df)) {
  valid <- !is.na(df$Hasford_Risk) & !is.na(df$ELTS_Risk)
  if(sum(valid) > 0) {
    pct <- round(mean(df$Hasford_Risk[valid] == df$ELTS_Risk[valid]) * 100, 1)
    conc_list[[length(conc_list)+1]] <- data.frame(Comparison = "Hasford vs ELTS", Agreement_Percent = pct, N_Evaluated = sum(valid))
  }
}

if(length(conc_list) > 0) {
  conc_df <- bind_rows(conc_list)
  ft_conc <- flextable(conc_df) %>%
    set_caption(caption = "CML Scores Concordance (% Agreement)") %>%
    autofit()
  doc_conc <- read_docx() %>%
    body_add_flextable(value = ft_conc)
  print(doc_conc, target = file.path(out_dir, "Tables", "CML_Scores_Concordance.docx"))
  cat("Concordance table saved to Tables/CML_Scores_Concordance.docx\n")
} else {
  cat("Not enough score comparisons computed, skipping Concordance Table.\n")
}

# Generate KM Plots
if(!is.null(col_os_time) && !is.null(col_os_stat)) {
  df$OS_time_num <- as.numeric(df[[col_os_time]])
  df$OS_stat_num <- as.numeric(df[[col_os_stat]])
  
  for(sc in c("Sokal", "Hasford", "ELTS")) {
    risk_col <- paste0(sc, "_Risk")
    if(risk_col %in% colnames(df)) {
      df_plot <- df[!is.na(df[[risk_col]]) & !is.na(df$OS_time_num) & !is.na(df$OS_stat_num), ]
      
      if(nrow(df_plot) > 0 && length(unique(df_plot[[risk_col]])) > 1) {
        fit <- survfit(as.formula(paste("Surv(OS_time_num, OS_stat_num) ~", risk_col)), data = df_plot)
        
        p <- ggsurvplot(fit, data=df_plot, pval=TRUE, conf.int=FALSE,
                        title=paste("Kaplan-Meier OS by", sc, "Risk"),
                        legend.title="Risk Group")
                        
        plot_path <- file.path(out_dir, "Figures", paste0("KM_", sc, ".eps"))
        setEPS()
        postscript(plot_path, width = 8, height = 6)
        print(p)
        dev.off()
        cat("Saved KM plot for", sc, "to", plot_path, "\n")
      } else {
        cat("Not enough data or variation in risk groups to plot KM for", sc, "\n")
      }
    }
  }
} else {
  warning("OS_time or OS_status columns not found or mismatched. Skipping KM plots.")
}

cat("CML Scoring script completed successfully.\n")