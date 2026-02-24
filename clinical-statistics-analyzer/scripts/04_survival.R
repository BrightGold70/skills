# Script: Survival and Competing Risks Analysis
# Purpose: Kaplan-Meier plots, Cox proportional hazards models, and Competing Risks (Cumulative Incidence)

library(survival)
library(survminer)
library(cmprsk)

args <- commandArgs(trailingOnly = TRUE)
if(length(args) < 3) {
  stop("Usage: Rscript 04_survival.R <dataset_path> <time_var> <status_var>")
}

input_data_path <- args[1]
time_var <- args[2]
status_var <- args[3] # Usually 0 = censor, 1 = event (or multiple codes for competing risks)

output_dir <- "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer"
plots_dir <- file.path(output_dir, "Figures")
if(!dir.exists(plots_dir)) dir.create(plots_dir, recursive = TRUE)

df <- read.csv(input_data_path)

# --- Survival Analysis (Kaplan-Meier) ---
formula_km <- paste("Surv(", time_var, ",", status_var, ") ~ Treatment")

if("Treatment" %in% names(df)) {
  fit <- survfit(as.formula(formula_km), data = df)
  
  km_plot <- ggsurvplot(fit, data = df, pval = TRUE, conf.int = TRUE,
                        risk.table = TRUE,
                        ggtheme = theme_minimal(),
                        title = paste("Kaplan-Meier Curve:", time_var))
  
  eps_file <- file.path(plots_dir, paste0("KM_Plot_", time_var, ".eps"))
  ggsave(filename = eps_file, print(km_plot), device = "eps", width = 8, height = 6)
  cat("Kaplan-Meier plot saved to:", eps_file, "\n")
  
  # --- Cox Proportional Hazards Model ---
  cox_model <- coxph(as.formula(formula_km), data = df)
  print(summary(cox_model))
} else {
  cat("No 'Treatment' column found. Skipping KM comparison.\n")
}

# --- Competing Risks Analysis (Cumulative Incidence) ---
# Assuming status_var has codes: 0=censor, 1=Event of Interest, 2=Competing Event
unique_statuses <- unique(df[[status_var]])
if(length(unique_statuses) > 2) {
  cat("More than 2 status codes detected. Assuming competing risks setup.\n")
  
  if("Treatment" %in% names(df)){
    ci_fit <- cuminc(ftime = df[[time_var]], fstatus = df[[status_var]], group = df$Treatment)
    
    eps_file_cr <- file.path(plots_dir, paste0("Cumulative_Incidence_", time_var, ".eps"))
    postscript(file = eps_file_cr, width = 8, height = 6)
    plot(ci_fit, xlab = "Time", ylab = "Cumulative Incidence", main = paste("Competing Risks:", time_var))
    dev.off()
    cat("Cumulative Incidence plot saved to:", eps_file_cr, "\n")
  }
}

cat("Survival analysis script completed.\n")
