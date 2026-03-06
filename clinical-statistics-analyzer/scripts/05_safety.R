# Script: Safety & Toxicity Analysis
# Purpose: Generate summaries of Adverse Events (AEs) with frequency thresholding

library(dplyr)
library(tidyr)
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
if(length(args) < 1) {
  stop("Usage: Rscript 05_safety.R <dataset_path> [frequency_threshold]")
}

input_data_path <- args[1]
freq_threshold <- ifelse(length(args) >= 2, as.numeric(args[2]), 0.10) # default 10%

output_dir <- Sys.getenv("CSA_OUTPUT_DIR", "")
if (output_dir == "") stop("CSA_OUTPUT_DIR not set. Export it first: export CSA_OUTPUT_DIR=/path/to/output")
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

# ── Emit stats sidecar ────────────────────────────────────────────────────────
tryCatch({
  stats_list <- list(n_total = nrow(df))
  grade_col <- intersect(c("Grade", "AE_Grade", "Toxicity_Grade", "CTCAE_Grade"), names(df))[1]
  if (!is.na(grade_col)) {
    g <- suppressWarnings(as.numeric(df[[grade_col]]))
    stats_list$ae_any_rate        <- list(value=round(mean(g > 0, na.rm=TRUE)*100, 1), unit="percent")
    stats_list$ae_grade3plus_rate <- list(value=round(mean(g >= 3, na.rm=TRUE)*100, 1), unit="percent")
    stats_list$ae_grade4plus_rate <- list(value=round(mean(g >= 4, na.rm=TRUE)*100, 1), unit="percent")
    stats_list$ae_fatal_rate      <- list(value=round(mean(g >= 5, na.rm=TRUE)*100, 1), unit="percent")
  }
  disc_col <- intersect(c("Discontinued", "Discontinuation", "Drug_Discontinued"), names(df))[1]
  if (!is.na(disc_col)) {
    stats_list$discontinuation_rate <- list(value=round(mean(df[[disc_col]] %in% c(1,TRUE,"1","Yes"), na.rm=TRUE)*100, 1), unit="percent")
  }
  dose_col <- intersect(c("DoseReduction", "Dose_Reduction", "Dose_Reduced"), names(df))[1]
  if (!is.na(dose_col)) {
    stats_list$dose_reduction_rate <- list(value=round(mean(df[[dose_col]] %in% c(1,TRUE,"1","Yes"), na.rm=TRUE)*100, 1), unit="percent")
  }
  write_stats_json(
    key_statistics = stats_list,
    analysis_notes = list(
      ctcae_version = "CTCAE v5.0",
      threshold     = paste0("AEs reported in >=", freq_threshold*100, "% of patients")
    )
  )
}, error = function(e) message("[write_stats_json] Skipped (error): ", e$message))
