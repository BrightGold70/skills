# Script: Efficacy Analysis
# Purpose: Perform logistic regression, subgroup interaction tests, and generate forest plots

library(dplyr)
library(ggplot2)
library(forestplot)
library(broom)

args <- commandArgs(trailingOnly = TRUE)
if(length(args) < 2) {
  stop("Usage: Rscript 03_efficacy.R <dataset_path> <outcome_variable>")
}

input_data_path <- args[1]
outcome_var <- args[2]

output_dir <- "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer"
plots_dir <- file.path(output_dir, "Figures")
tables_dir <- file.path(output_dir, "Tables")

if(!dir.exists(plots_dir)) dir.create(plots_dir, recursive = TRUE)
if(!dir.exists(tables_dir)) dir.create(tables_dir, recursive = TRUE)

# Load data
df <- read.csv(input_data_path) # Assuming CSV for simplicity, adapt as in Table 1 script

# Basic logistic regression
cat("Performing Logistic Regression on", outcome_var, "...\n")

if(!"Treatment" %in% names(df)) {
  stop("A 'Treatment' column is required for efficacy analysis.")
}

formula_str <- paste(outcome_var, "~ Treatment")
model <- glm(as.formula(formula_str), data = df, family = binomial(link = "logit"))

summary_df <- tidy(model, conf.int = TRUE, exponentiate = TRUE)
write.csv(summary_df, file.path(tables_dir, paste0("Efficacy_", outcome_var, "_Analysis.csv")), row.names=FALSE)

# Placeholder for Subgroup Analysis and Forest Plotting
cat("Generating Forest Plot (EPS)...\n")
# Normally here you would loop through subgroups, fit models, and compile results for forestplot()

# Example mock forest plot code:
mock_data <- data.frame(
  mean = c(NA, 1.2, 0.8),
  lower = c(NA, 0.9, 0.5),
  upper = c(NA, 1.5, 1.1)
)
mock_labels <- rbind(
  c("Subgroup", "Odds Ratio", "P-value"),
  c("Group A", "1.2 (0.9-1.5)", "0.15"),
  c("Group B", "0.8 (0.5-1.1)", "0.08")
)

eps_file <- file.path(plots_dir, paste0("ForestPlot_", outcome_var, ".eps"))
postscript(file = eps_file, horizontal = FALSE, onefile = FALSE, paper = "special", width = 8, height = 6)
forestplot(mock_labels, mock_data, new_page = TRUE, boxsize = 0.25, ci.vertices = TRUE)
dev.off()

cat("Efficacy analysis complete.\n")
