# Script: Safety & Toxicity Analysis
# Purpose: Generate summaries of Adverse Events (AEs) with frequency thresholding

library(dplyr)
library(tidyr)
library(flextable)
library(officer)

args <- commandArgs(trailingOnly = TRUE)
if(length(args) < 1) {
  stop("Usage: Rscript 05_safety.R <dataset_path> [frequency_threshold]")
}

input_data_path <- args[1]
freq_threshold <- ifelse(length(args) >= 2, as.numeric(args[2]), 0.10) # default 10%

output_dir <- "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer"
tables_dir <- file.path(output_dir, "Tables")
if(!dir.exists(tables_dir)) dir.create(tables_dir, recursive = TRUE)

df <- read.csv(input_data_path)

if(!"Treatment" %in% names(df)) {
  stop("A 'Treatment' column is required for safety summarization.")
}

# Assuming dataset is in long format: PatientID, Treatment, AE_Term, Grade
# Or wide format with binary columns for specific AEs.
# Here we mock a basic wide-to-long assumption or direct frequency count if AEs start with certain prefix

cat("Calculating Adverse Event frequencies (threshold >=", freq_threshold*100, "%)...\n")

# Mock process for calculating AE frequencies:
# Find columns containing "AE_" or "Tox_"
ae_cols <- grep("^(AE_|Tox_)", names(df), value = TRUE)

if(length(ae_cols) > 0) {
  # Calculate frequency of AEs by treatment
  ae_summary <- df %>%
    group_by(Treatment) %>%
    summarise(across(all_of(ae_cols), ~ mean(. > 0, na.rm = TRUE))) %>%
    pivot_longer(cols = -Treatment, names_to = "Adverse_Event", values_to = "Frequency") %>%
    filter(Frequency >= freq_threshold) %>%
    pivot_wider(names_from = Treatment, values_from = Frequency)
  
  # Format as flex table
  ft <- flextable(ae_summary) %>%
    autofit() %>%
    set_caption(paste("Adverse Events Summary (>= ", freq_threshold*100, "%)"))
  
  doc <- read_docx()
  doc <- body_add_flextable(doc, value = ft)
  
  output_file <- file.path(tables_dir, "Safety_Summary_Table.docx")
  print(doc, target = output_file)
  cat("Safety summary table saved to:", output_file, "\n")
  
} else {
  cat("No columns matching 'AE_' or 'Tox_' were found to summarize.\n")
}
