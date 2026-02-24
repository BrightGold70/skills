# Script: Table 1 (Baseline Characteristics) Generator
# Purpose: Generate standard baseline characteristic tables comparing treatment arms.

library(table1)
library(dplyr)
library(flextable)
library(officer)

args <- commandArgs(trailingOnly = TRUE)
if(length(args) == 0) {
  stop("Please provide the path to the dataset as an argument.")
}

input_data_path <- args[1]
output_dir <- "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer"
data_dir <- file.path(output_dir, "data")
tables_dir <- file.path(output_dir, "Tables")

if(!dir.exists(tables_dir)) dir.create(tables_dir, recursive = TRUE)

# Load data based on extension
if (grepl("\\.xlsx$", input_data_path, ignore.case = TRUE)) {
  library(readxl)
  df <- read_excel(input_data_path)
} else if (grepl("\\.sav$", input_data_path, ignore.case = TRUE)) {
  library(haven)
  df <- read_sav(input_data_path)
} else if (grepl("\\.rds$", input_data_path, ignore.case = TRUE)) {
  df <- readRDS(input_data_path)
} else if (grepl("\\.csv$", input_data_path, ignore.case = TRUE)) {
  df <- read.csv(input_data_path)
} else {
  stop("Unsupported file format. Please use .xlsx, .sav, .rds, or .csv")
}

# Ensure there is a Treatment/Arm column (Replace 'Treatment' with actual column name if needed)
if(!"Treatment" %in% names(df) && !"Arm" %in% names(df)){
  warning("No 'Treatment' or 'Arm' column found. Defaulting to first column as grouping variable if appropriate.")
  group_var <- names(df)[1]
} else {
  group_var <- ifelse("Treatment" %in% names(df), "Treatment", "Arm")
}

# Generate Table 1
formula_str <- paste("~ . |", group_var)
tb1 <- table1(as.formula(formula_str), data = df)

# Convert to flextable and save as docx
ft <- t1flex(tb1)
doc <- read_docx()
doc <- body_add_flextable(doc, value = ft)

output_file <- file.path(tables_dir, "Table1_Baseline_Characteristics.docx")
print(doc, target = output_file)

cat("Table 1 generated successfully and saved to:", output_file, "\n")
