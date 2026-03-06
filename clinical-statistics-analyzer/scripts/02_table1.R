# Script: Table 1 (Baseline Characteristics) Generator
# Purpose: Generate standard baseline characteristic tables comparing treatment arms.

library(table1)
library(dplyr)
library(flextable)
library(officer)

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
if(length(args) == 0) {
  stop("Please provide the path to the dataset as an argument.")
}

input_data_path <- args[1]
output_dir <- Sys.getenv("CSA_OUTPUT_DIR", "")
if (output_dir == "") stop("CSA_OUTPUT_DIR not set. Export it first: export CSA_OUTPUT_DIR=/path/to/output")
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

# ── Emit stats sidecar ────────────────────────────────────────────────────────
tryCatch({
  sex_col <- intersect(c("Sex", "Gender"), names(df))[1]
  ecog_col <- intersect(c("ECOG", "ECOG_PS", "Performance_Status"), names(df))[1]
  fu_col   <- intersect(c("Follow_Up", "Follow_Up_Months", "FU_Months"), names(df))[1]
  write_stats_json(
    key_statistics = list(
      n_total           = nrow(df),
      age_median        = if ("Age" %in% names(df)) round(median(df$Age, na.rm=TRUE), 1) else NULL,
      age_iqr_lower     = if ("Age" %in% names(df)) round(quantile(df$Age, 0.25, na.rm=TRUE), 1) else NULL,
      age_iqr_upper     = if ("Age" %in% names(df)) round(quantile(df$Age, 0.75, na.rm=TRUE), 1) else NULL,
      sex_male_rate     = if (!is.na(sex_col)) list(value=round(mean(df[[sex_col]] %in% c("Male","M","1",1), na.rm=TRUE)*100,1), unit="percent") else NULL,
      ecog_0_1_rate     = if (!is.na(ecog_col)) list(value=round(mean(df[[ecog_col]] <= 1, na.rm=TRUE)*100,1), unit="percent") else NULL,
      follow_up_median_months = if (!is.na(fu_col)) list(value=round(median(df[[fu_col]], na.rm=TRUE),1), unit="months") else NULL
    ),
    analysis_notes = list()
  )
}, error = function(e) message("[write_stats_json] Skipped (error): ", e$message))
