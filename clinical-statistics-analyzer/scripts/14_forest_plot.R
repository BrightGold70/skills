# Script: Forest Plot Generation for Subgroup Analysis
# Purpose: Generate publication-ready forest plots for subgroup analyses
# Uses: survival, survminer, ggplot2, forestplot
# Output: .eps forest plot + .csv results

library(survival)
library(survminer)
library(ggplot2)
library(forestplot)
library(broom)
library(dplyr)

# ==============================================================================
# COMMAND LINE ARGUMENTS
# ==============================================================================

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 4) {
  cat("Usage: Rscript 14_forest_plot.R <data_file> <time_var> <status_var> <subgroup_vars> [treatment_var] [output_dir]\n")
  cat("\nArguments:\n")
  cat("  data_file      : Path to CSV/Excel dataset\n")
  cat("  time_var       : Time-to-event variable (e.g., OS_MONTHS)\n")
  cat("  status_var     : Event status variable (e.g., OS_STATUS, 1=event)\n")
  cat("  subgroup_vars  : Comma-separated subgroup variables (e.g., AGE,SEX,CYTOGENETICS)\n")
  cat("  treatment_var  : Treatment variable name (default: Treatment)\n")
  cat("  output_dir     : Output directory (default: Figures/)\n")
  cat("\nExample:\n")
  cat("  Rscript 14_forest_plot.R data.csv OS_MONTHS OS_STATUS \"AGE_GRP,SEX,CYTO\" Treatment\n")
  stop()
}

data_file <- args[1]
time_var <- args[2]
status_var <- args[3]
subgroup_vars <- strsplit(args[4], ",")[[1]]
treatment_var <- ifelse(length(args) >= 5, args[5], "Treatment")
output_dir <- ifelse(length(args) >= 6, args[6], "Figures")

# ==============================================================================
# OUTPUT DIRECTORY
# ==============================================================================

output_base <- Sys.getenv("CSA_OUTPUT_DIR", "")
if (output_base == "") stop("CSA_OUTPUT_DIR not set. Export it first: export CSA_OUTPUT_DIR=/path/to/output")
tables_dir <- file.path(output_base, "Tables")
plots_dir <- file.path(output_base, output_dir)

if (!dir.exists(tables_dir)) dir.create(tables_dir, recursive = TRUE)
if (!dir.exists(plots_dir)) dir.create(plots_dir, recursive = TRUE)

# ==============================================================================
# LOAD DATA
# ==============================================================================

cat("Loading data from:", data_file, "\n")

if (grepl("\\.xlsx$", data_file, ignore.case = TRUE)) {
  library(readxl)
  df <- read_excel(data_file)
} else if (grepl("\\.csv$", data_file, ignore.case = TRUE)) {
  df <- read.csv(data_file, stringsAsFactors = FALSE)
} else {
  stop("Unsupported file format. Use .csv or .xlsx")
}

cat("Data loaded:", nrow(df), "rows,", ncol(df), "columns\n")

# Check required columns
required_cols <- c(time_var, status_var, treatment_var, subgroup_vars)
missing <- required_cols[!required_cols %in% names(df)]
if (length(missing) > 0) {
  stop(sprintf("Missing required columns: %s", paste(missing, collapse = ", ")))
}

# ==============================================================================
# SUBGROUP ANALYSIS FUNCTION
# ==============================================================================

#' Perform subgroup analysis for a single variable
#' @param data Dataset
#' @param var Subgroup variable
#' @param time_var Time variable
#' @param status_var Status variable
#' @param treatment_var Treatment variable
#' @return List with results
subgroup_analysis <- function(data, var, time_var, status_var, treatment_var) {
  
  # Get unique values (excluding NA)
  levels <- unique(data[[var]])
  levels <- levels[!is.na(levels)]
  
  if (length(levels) < 2) {
    return(NULL)
  }
  
  results <- list()
  
  for (level in levels) {
    # Subset data for this level
    subset_data <- data[data[[var]] == level, ]
    
    # Skip if too few events
    n_events <- sum(subset_data[[status_var]] == 1, na.rm = TRUE)
    if (n_events < 5) {
      next
    }
    
    # Fit Cox model
    formula_str <- paste0("Surv(", time_var, ",", status_var, ") ~ ", treatment_var)
    fit <- tryCatch(
      coxph(as.formula(formula_str), data = subset_data),
      error = function(e) NULL
    )
    
    if (is.null(fit)) {
      next
    }
    
    # Extract results
    sum_fit <- summary(fit)
    hr <- sum_fit$coefficients[1, "exp(coef)"]
    lower <- sum_fit$conf.int[1, "lower .95"]
    upper <- sum_fit$conf.int[1, "upper .95"]
    pval <- sum_fit$coefficients[1, "Pr(>|z|)"]
    
    results[[as.character(level)]] <- list(
      subgroup = var,
      level = level,
      n = nrow(subset_data),
      events = n_events,
      hr = hr,
      lower = lower,
      upper = upper,
      pvalue = pval
    )
  }
  
  return(results)
}

#' Test for interaction between treatment and subgroup
#' @param data Dataset
#' @param var Subgroup variable
#' @param time_var Time variable
#' @param status_var Status variable
#' @param treatment_var Treatment variable
#' @return Interaction p-value
test_interaction <- function(data, var, time_var, status_var, treatment_var) {
  formula_str <- paste0("Surv(", time_var, ",", status_var, ") ~ ", 
                        treatment_var, "*", var)
  fit <- tryCatch(
    coxph(as.formula(formula_str), data = data),
    error = function(e) NULL
  )
  
  if (is.null(fit)) {
    return(NA)
  }
  
  # Get interaction term coefficient
  interaction_term <- paste0(treatment_var, ":", var)
  if (interaction_term %in% names(coef(fit))) {
    sum_fit <- summary(fit)
    p_interaction <- sum_fit$coefficients[interaction_term, "Pr(>|z|)"]
    return(p_interaction)
  }
  
  return(NA)
}

# ==============================================================================
# RUN SUBGROUP ANALYSES
# ==============================================================================

cat("\n========================================\n")
cat("Running Subgroup Analyses\n")
cat("========================================\n\n")

all_results <- list()
interaction_pvals <- c()

for (var in subgroup_vars) {
  cat(sprintf("Analyzing subgroup: %s\n", var))
  
  # Interaction test
  p_interact <- test_interaction(df, var, time_var, status_var, treatment_var)
  interaction_pvals[var] <- p_interact
  cat(sprintf("  Interaction p-value: %.4f\n", p_interact))
  
  # Stratified analysis
  res <- subgroup_analysis(df, var, time_var, status_var, treatment_var)
  if (!is.null(res)) {
    all_results[[var]] <- res
  }
}

# ==============================================================================
# COMBINE RESULTS
# ==============================================================================

# Create results dataframe
results_list <- list()

for (subgroup_name in names(all_results)) {
  for (level_name in names(all_results[[subgroup_name]])) {
    r <- all_results[[subgroup_name]][[level_name]]
    results_list[[length(results_list) + 1]] <- data.frame(
      subgroup = r$subgroup,
      level = r$level,
      n = r$n,
      events = r$events,
      hr = r$hr,
      lower = r$lower,
      upper = r$upper,
      pvalue = r$pvalue,
      stringsAsFactors = FALSE
    )
  }
}

if (length(results_list) == 0) {
  cat("No valid subgroup results. Check data and subgroup variables.\n")
  stop("No results")
}

results_df <- do.call(rbind, results_list)

# Add interaction p-values
results_df$interaction_pval <- sapply(results_df$subgroup, function(s) interaction_pvals[s])

# Add overall row
overall_formula <- paste0("Surv(", time_var, ",", status_var, ") ~ ", treatment_var)
overall_fit <- coxph(as.formula(overall_formula), data = df)
overall_sum <- summary(overall_fit)

overall_row <- data.frame(
  subgroup = "Overall",
  level = "All",
  n = nrow(df),
  events = sum(df[[status_var]] == 1, na.rm = TRUE),
  hr = overall_sum$coefficients[1, "exp(coef)"],
  lower = overall_sum$conf.int[1, "lower .95"],
  upper = overall_sum$conf.int[1, "upper .95"],
  pvalue = overall_sum$coefficients[1, "Pr(>|z|)"],
  interaction_pval = NA,
  stringsAsFactors = FALSE
)

results_df <- rbind(overall_row, results_df)

# Sort by subgroup
results_df <- results_df[order(results_df$subgroup, results_df$level), ]

cat("\nResults:\n")
print(results_df)

# ==============================================================================
# CREATE FOREST PLOT
# ==============================================================================

cat("\n========================================\n")
cat("Generating Forest Plot\n")
cat("========================================\n")

# Prepare data for forestplot
plot_data <- results_df[!is.na(results_df$hr), ]

# Create label column
plot_data$label <- paste0(plot_data$subgroup, ": ", plot_data$level)

# Calculate log HR for plotting
plot_data$log_hr <- log(plot_data$hr)
plot_data$log_lower <- log(plot_data$lower)
plot_data$log_upper <- log(plot_data$upper)

# Format HR with CI for display
plot_data$hr_display <- sprintf("%.2f (%.2f-%.2f)", 
                                 plot_data$hr, plot_data$lower, plot_data$upper)
plot_data$p_display <- ifelse(plot_data$pvalue < 0.001, "<0.001", 
                               sprintf("%.3f", plot_data$pvalue))

# Create forest plot using ggplot2
p <- ggplot(plot_data, aes(x = hr, y = label)) +
  geom_point(shape = 15, size = 3) +
  geom_errorbar(aes(xmin = lower, xmax = upper), width = 0.3) +
  geom_vline(xintercept = 1, linetype = "dashed", color = "red") +
  scale_x_log10() +
  labs(
    title = "Forest Plot: Subgroup Analysis",
    subtitle = paste("Hazard Ratio (", treatment_var, "vs Control)"),
    x = "Hazard Ratio (log scale)",
    y = ""
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(hjust = 0.5, size = 14, face = "bold"),
    plot.subtitle = element_text(hjust = 0.5, size = 10),
    axis.text.y = element_text(size = 10),
    axis.text.x = element_text(size = 10)
  )

# Save as EPS
eps_file <- file.path(plots_dir, paste0("ForestPlot_", gsub("_", "", time_var), ".eps"))
ggsave(filename = eps_file, plot = p, device = "eps", width = 10, height = max(6, nrow(plot_data) * 0.5))
cat(sprintf("Forest plot saved to: %s\n", eps_file))

# ==============================================================================
# SAVE RESULTS
# ==============================================================================

# Save CSV
csv_file <- file.path(tables_dir, paste0("SubgroupAnalysis_", time_var, ".csv"))
write.csv(results_df, csv_file, row.names = FALSE)
cat(sprintf("Results saved to: %s\n", csv_file))

# ==============================================================================
# SUMMARY TABLE
# ==============================================================================

cat("\n========================================\n")
cat("SUMMARY\n")
cat("========================================\n")

# Find significant subgroups (p < 0.05)
sig_subgroups <- results_df[results_df$pvalue < 0.05 & !is.na(results_df$pvalue), ]
if (nrow(sig_subgroups) > 0) {
  cat("\nSignificant subgroups (p < 0.05):\n")
  for (i in 1:nrow(sig_subgroups)) {
    r <- sig_subgroups[i, ]
    cat(sprintf("  - %s: %s - HR = %.2f (%.2f-%.2f), p = %.4f\n",
                r$subgroup, r$level, r$hr, r$lower, r$upper, r$pvalue))
  }
}

# Interaction results
cat("\nTreatment-by-subgroup interaction tests:\n")
for (var in names(interaction_pvals)) {
  p <- interaction_pvals[var]
  sig <- ifelse(p < 0.05, "*", "")
  cat(sprintf("  - %s: p = %.4f %s\n", var, p, sig))
}

cat("\nDone.\n")
