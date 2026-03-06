#!/usr/bin/env Rscript

# 20_aml_eln_risk.R
# Auto-classifies AML patients into ELN 2022 risk categories
# Reference: Döhner H et al. Blood. 2022;140(12):1345-1377.

suppressPackageStartupMessages({
  library(dplyr)
  library(officer)
  library(flextable)
  library(ggplot2)
  library(readxl)
  library(haven)
})

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

# Function to safely load data based on extension
load_data <- function(filepath) {
  if (!file.exists(filepath)) {
    stop("File not found: ", filepath)
  }
  
  ext <- tools::file_ext(filepath)
  
  if (tolower(ext) %in% c("csv")) {
    return(read.csv(filepath, stringsAsFactors = FALSE))
  } else if (tolower(ext) %in% c("xlsx", "xls")) {
    return(read_excel(filepath))
  } else if (tolower(ext) %in% c("sav", "zsav")) {
    return(read_sav(filepath))
  } else if (tolower(ext) %in% c("rda", "rdata")) {
    env <- new.env()
    load(filepath, envir = env)
    # Return the first data frame found
    dfs <- Filter(is.data.frame, as.list(env))
    if (length(dfs) > 0) return(dfs[[1]])
    stop("No data frame found in RData file.")
  } else if (tolower(ext) %in% c("rds")) {
    return(readRDS(filepath))
  } else {
    stop("Unsupported file extension: ", ext)
  }
}

# Parse command line args
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  stop("Usage: Rscript 20_aml_eln_risk.R <dataset_path>")
}
dataset_path <- args[1]

# Load dataset
cat("Loading dataset:", dataset_path, "\n")
df <- load_data(dataset_path)

# Ensure ID column exists or create one
if (!"ID" %in% names(df) && !"Patient_ID" %in% names(df)) {
  df$Patient_ID <- 1:nrow(df)
}

# Define required ELN 2022 columns
required_cols <- c("t_8_21", "RUNX1_RUNX1T1", "inv16", "CBFB_MYH11", "NPM1_mut", "FLT3_ITD", 
                   "CEBPA_biallelic", "PML_RARA", "DEK_NUP214", "KMT2A_r", "BCR_ABL1_AML", 
                   "KAT6A_CREBBP", "inv3_t3_3", "del5q", "monosomy7", "abn17p", 
                   "complex_karyotype", "monosomal_karyotype", "ASXL1_mut", "BCOR_mut", 
                   "EZH2_mut", "SF3B1_mut", "SRSF2_mut", "STAG2_mut", "U2AF1_mut", 
                   "ZRSR2_mut", "TP53_biallelic", "FLT3_ITD_VAF")

# Helper: convert SPSS-labeled values to logical
to_logical <- function(x) {
  if (is.logical(x)) return(x)
  if (is.numeric(x)) return(x == 1)
  tolower(as.character(x)) %in% c("true", "yes", "1", "positive", "detected", "mutated")
}

# Check how many ELN columns are available
missing_cols <- setdiff(required_cols, names(df))
available_eln <- length(required_cols) - length(missing_cols)
total_eln <- length(required_cols)
use_simplified <- (available_eln / total_eln) < 0.5

if (length(missing_cols) == length(required_cols)) {
  warning("ALL ELN 2022 classification columns are missing from the dataset. Cannot determine risk.")
} else if (use_simplified) {
  cat("WARNING: Only", available_eln, "of", total_eln,
      "ELN-relevant columns available. Using simplified classification.\n")
  cat("Available:", paste(required_cols[required_cols %in% names(df)], collapse=", "), "\n")
  cat("Missing:", paste(missing_cols, collapse=", "), "\n\n")

  # Simplified classification using available core markers
  df$ELN2022_Risk <- "Intermediate"
  if ("NPM1_mut" %in% names(df) & "FLT3_ITD" %in% names(df)) {
    npm1_pos <- to_logical(df$NPM1_mut)
    flt3_pos <- to_logical(df$FLT3_ITD)
    df$ELN2022_Risk[npm1_pos & !flt3_pos] <- "Favorable"
  }
  if ("TP53_mut" %in% names(df)) {
    tp53_pos <- to_logical(df$TP53_mut)
    df$ELN2022_Risk[tp53_pos] <- "Adverse"
  }
  if ("TP53_biallelic" %in% names(df)) {
    tp53b <- to_logical(df$TP53_biallelic)
    df$ELN2022_Risk[tp53b] <- "Adverse"
  }
  if ("complex_karyotype" %in% names(df)) {
    ck <- to_logical(df$complex_karyotype)
    df$ELN2022_Risk[ck] <- "Adverse"
  }

  df$ELN_Note <- paste0("Simplified (", available_eln, "/", total_eln, " markers)")
  cat("Simplified classification complete. Distribution:\n")
  print(table(df$ELN2022_Risk))

} else if (length(missing_cols) > 0) {
  warning(paste("The following required columns are missing and will be treated as FALSE/0:\n",
                paste(missing_cols, collapse=", ")))
}

# Fill missing columns (needed for full classification path and summary table)
for (col in missing_cols) {
  if (col == "FLT3_ITD_VAF") {
    df[[col]] <- 0
  } else {
    df[[col]] <- FALSE
  }
}

# Skip full classification if using simplified mode
if (!use_simplified) {

# Also handle NA values in existing columns to prevent NA evaluation
# We need to track patients where ALL relevant columns are NA
all_na <- rep(TRUE, nrow(df))

for (col in required_cols) {
  if (col %in% names(df)) {
    # If any column is not NA, then not all are NA
    all_na <- all_na & is.na(df[[col]])
    
    # Impute NAs with FALSE/0
    if (col == "FLT3_ITD_VAF") {
      df[[col]][is.na(df[[col]])] <- 0
    } else {
      # Handle NA
      df[[col]][is.na(df[[col]])] <- FALSE
      # If character "TRUE"/"FALSE", convert to logical
      if (is.character(df[[col]])) {
        df[[col]] <- tolower(df[[col]]) %in% c("true", "t", "yes", "y", "1")
      } else if (is.numeric(df[[col]])) {
        df[[col]] <- df[[col]] > 0
      }
    }
  }
}

# Log warning for patients where classification could not be determined
if (any(all_na)) {
  warning(sprintf("Could not determine classification for %d patient(s) due to all NA values. Defaulting to Intermediate.", sum(all_na)))
}

# Apply ELN 2022 Logic
# 1. Base conditions
is_cbf_apl <- df$t_8_21 | df$RUNX1_RUNX1T1 | df$inv16 | df$CBFB_MYH11 | df$PML_RARA

is_adverse <- df$DEK_NUP214 | df$KMT2A_r | df$BCR_ABL1_AML | df$KAT6A_CREBBP | 
              df$inv3_t3_3 | df$del5q | df$monosomy7 | df$abn17p | 
              df$complex_karyotype | df$monosomal_karyotype | df$ASXL1_mut | 
              df$BCOR_mut | df$EZH2_mut | df$SF3B1_mut | df$SRSF2_mut | 
              df$STAG2_mut | df$U2AF1_mut | df$ZRSR2_mut | df$TP53_biallelic | 
              (df$NPM1_mut & df$FLT3_ITD_VAF >= 0.5)

is_other_fav <- (df$NPM1_mut & !df$FLT3_ITD) | df$CEBPA_biallelic

# 2. Assign categories with correct precedence
# Precedence: 
# a. CBF/APL overrides all -> Favorable
# b. Adverse overrides other Favorable (NPM1/CEBPA) and Intermediate
# c. Other Favorable -> Favorable
# d. Else -> Intermediate
df$ELN2022_Risk <- "Intermediate"
df$ELN2022_Risk[is_other_fav] <- "Favorable"
df$ELN2022_Risk[is_adverse] <- "Adverse"
df$ELN2022_Risk[is_cbf_apl] <- "Favorable"

# Convert to factor for correct ordering
df$ELN2022_Risk <- factor(df$ELN2022_Risk, levels = c("Favorable", "Intermediate", "Adverse"))

cat("Classification complete. Distribution:\n")
print(table(df$ELN2022_Risk))

} # end if (!use_simplified)

# Output generation
base_dir <- Sys.getenv("CSA_OUTPUT_DIR", "")
if (base_dir == "") stop("CSA_OUTPUT_DIR not set. Export it first: export CSA_OUTPUT_DIR=/path/to/output")
tables_dir <- file.path(base_dir, "Tables")
figures_dir <- file.path(base_dir, "Figures")
data_dir <- file.path(base_dir, "data")

if (!dir.exists(tables_dir)) dir.create(tables_dir, recursive = TRUE)
if (!dir.exists(figures_dir)) dir.create(figures_dir, recursive = TRUE)
if (!dir.exists(data_dir)) dir.create(data_dir, recursive = TRUE)

# 1. Output Table (docx)
cat("Generating docx table...\n")
summary_df <- df %>%
  group_by(ELN2022_Risk) %>%
  summarise(
    N = n(),
    `CBF/APL` = sum(t_8_21 | RUNX1_RUNX1T1 | inv16 | CBFB_MYH11 | PML_RARA, na.rm=TRUE),
    `NPM1 Mutated` = sum(NPM1_mut, na.rm=TRUE),
    `FLT3-ITD` = sum(FLT3_ITD, na.rm=TRUE),
    `TP53 Biallelic` = sum(TP53_biallelic, na.rm=TRUE),
    `Complex Karyotype` = sum(complex_karyotype, na.rm=TRUE)
  ) %>%
  mutate(
    `N (%)` = sprintf("%d (%.1f%%)", N, N / sum(N) * 100)
  ) %>%
  select(ELN2022_Risk, `N (%)`, `CBF/APL`, `NPM1 Mutated`, `FLT3-ITD`, `TP53 Biallelic`, `Complex Karyotype`) %>%
  rename(`ELN 2022 Risk` = ELN2022_Risk)

# Add totals row
totals <- df %>%
  summarise(
    `ELN 2022 Risk` = "Total",
    N = n(),
    `CBF/APL` = sum(t_8_21 | RUNX1_RUNX1T1 | inv16 | CBFB_MYH11 | PML_RARA, na.rm=TRUE),
    `NPM1 Mutated` = sum(NPM1_mut, na.rm=TRUE),
    `FLT3-ITD` = sum(FLT3_ITD, na.rm=TRUE),
    `TP53 Biallelic` = sum(TP53_biallelic, na.rm=TRUE),
    `Complex Karyotype` = sum(complex_karyotype, na.rm=TRUE)
  ) %>%
  mutate(`N (%)` = sprintf("%d (100.0%%)", N)) %>%
  select(`ELN 2022 Risk`, `N (%)`, `CBF/APL`, `NPM1 Mutated`, `FLT3-ITD`, `TP53 Biallelic`, `Complex Karyotype`)

summary_df <- bind_rows(summary_df, totals)

ft <- flextable(summary_df) %>%
  theme_vanilla() %>%
  autofit() %>%
  set_caption(caption = "AML ELN 2022 Risk Stratification") %>%
  bold(i = nrow(summary_df), bold = TRUE) # Bold totals row

table_path <- file.path(tables_dir, "AML_ELN2022_Risk_Stratification.docx")
doc <- read_docx() %>%
  body_add_flextable(value = ft) %>%
  print(target = table_path)
cat("Table saved to:", table_path, "\n")

# 2. Output Figure (eps)
cat("Generating eps plot...\n")
p <- ggplot(df, aes(x = ELN2022_Risk, fill = ELN2022_Risk)) +
  geom_bar(color = "black", alpha = 0.8) +
  geom_text(stat='count', aes(label=after_stat(count)), vjust=-0.5) +
  scale_fill_manual(values = c("Favorable" = "#4CAF50", "Intermediate" = "#FFC107", "Adverse" = "#F44336")) +
  theme_minimal() +
  labs(
    title = "AML ELN 2022 Risk Distribution", 
    x = "ELN 2022 Risk Category", 
    y = "Number of Patients"
  ) +
  theme(
    legend.position = "none",
    plot.title = element_text(hjust = 0.5, face = "bold", size = 14),
    axis.title = element_text(face = "bold"),
    axis.text = element_text(size = 11)
  )

figure_path <- file.path(figures_dir, "AML_ELN2022_Risk_Distribution.eps")
ggsave(filename = figure_path, plot = p, device = "eps", width = 8, height = 6)
cat("Figure saved to:", figure_path, "\n")

# 3. Save modified dataset
data_path <- file.path(data_dir, "aml_classified_data.csv")
write.csv(df, data_path, row.names = FALSE)
cat("Classified dataset saved to:", data_path, "\n")

cat("ELN 2022 Risk classification successfully completed.\n")

# ── Emit stats sidecar ────────────────────────────────────────────────────────
tryCatch({
  eln_tbl <- table(df$ELN2022_Risk)
  n_tot   <- nrow(df)
  pct_grp <- function(grp) if (grp %in% names(eln_tbl)) round(eln_tbl[[grp]] / n_tot * 100, 1) else NULL
  write_stats_json(
    key_statistics = list(
      n_total              = n_tot,
      eln_favorable_pct    = if (!is.null(pct_grp("Favorable")))    list(value = pct_grp("Favorable"),    unit = "percent") else NULL,
      eln_intermediate_pct = if (!is.null(pct_grp("Intermediate"))) list(value = pct_grp("Intermediate"), unit = "percent") else NULL,
      eln_adverse_pct      = if (!is.null(pct_grp("Adverse")))      list(value = pct_grp("Adverse"),      unit = "percent") else NULL
    ),
    analysis_notes   = list(reference = "Döhner H et al. Blood. 2022;140(12):1345-1377"),
    disease_specific = list(disease = "AML", classification = "ELN 2022")
  )
}, error = function(e) message("[write_stats_json] Skipped (error): ", e$message))
