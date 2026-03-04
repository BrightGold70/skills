#!/usr/bin/env Rscript
# 28_cml_resistance.R — ABL1 kinase domain mutation tracking
#
# Usage: Rscript 28_cml_resistance.R <dataset>
#
# Outputs:
#   Tables/CML_Resistance_Mutations.docx  — Mutation frequency table by TKI
#   Figures/CML_Resistance_Timeline.eps   — Patient timeline with mutation events

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(flextable)
  library(officer)
  library(lubridate)
})

# --- Parse arguments ---
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: Rscript 28_cml_resistance.R <dataset>")
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

# --- Filter patients with resistance mutations ---
required_cols <- c("Patient_ID", "resistance_mutation", "resistance_date", "Treatment_Start_Date")
missing_cols <- setdiff(required_cols, names(df))
if (length(missing_cols) > 0) {
  # Try alternative column name
  if ("Treatment" %in% names(df) && !"Treatment_Start_Date" %in% names(df)) {
    cat("Warning: Treatment_Start_Date not found, using approximate dates\n")
  }
}

resistance_df <- df %>%
  filter(!is.na(resistance_mutation) & resistance_mutation != "")

cat("Found", nrow(resistance_df), "patients with resistance mutations\n")

if (nrow(resistance_df) == 0) {
  cat("No resistance mutations found — generating empty outputs\n")

  # Empty table
  empty_ft <- flextable(data.frame(Mutation = "None detected", N = 0, `Pct` = "0%")) %>%
    set_caption("Table: ABL1 Kinase Domain Mutations") %>%
    theme_vanilla()

  doc <- read_docx() %>%
    body_add_par("ABL1 Kinase Domain Resistance Mutations", style = "heading 1") %>%
    body_add_par("No resistance mutations detected in this cohort.") %>%
    body_add_flextable(empty_ft)
  print(doc, target = file.path(tables_dir, "CML_Resistance_Mutations.docx"))

  cat("28_cml_resistance.R completed (no mutations found)\n")
  quit(save = "no", status = 0)
}

# --- Calculate time-to-resistance ---
if ("Treatment_Start_Date" %in% names(resistance_df) & "resistance_date" %in% names(resistance_df)) {
  resistance_df <- resistance_df %>%
    mutate(
      tx_start = as.Date(Treatment_Start_Date),
      res_date = as.Date(resistance_date),
      time_to_resistance_months = as.numeric(difftime(res_date, tx_start, units = "days")) / 30.44
    )
} else {
  resistance_df$time_to_resistance_months <- NA
}

# --- Identify clinically significant mutations ---
significant_mutations <- c("T315I", "T315I/E255K", "T315A", "F317L", "E255K", "E255V", "Y253H")

resistance_df <- resistance_df %>%
  mutate(
    is_compound = grepl("/", resistance_mutation),
    is_T315I = grepl("T315I", resistance_mutation),
    clinical_significance = case_when(
      is_T315I ~ "T315I (pan-resistant)",
      is_compound ~ "Compound mutation",
      resistance_mutation %in% significant_mutations ~ "Clinically significant",
      TRUE ~ "Other"
    )
  )

# --- Mutation frequency table ---
mutation_freq <- resistance_df %>%
  group_by(resistance_mutation) %>%
  summarise(
    N = n(),
    .groups = "drop"
  ) %>%
  mutate(
    Pct = sprintf("%.1f", N / nrow(resistance_df) * 100),
    `N (%)` = paste0(N, " (", Pct, "%)")
  ) %>%
  arrange(desc(N))

# By TKI if available
treatment_col <- if ("Treatment" %in% names(resistance_df)) "Treatment" else NULL

if (!is.null(treatment_col)) {
  by_tki <- resistance_df %>%
    group_by(Treatment, resistance_mutation) %>%
    summarise(N = n(), .groups = "drop") %>%
    tidyr::pivot_wider(
      names_from = Treatment,
      values_from = N,
      values_fill = 0
    )

  mutation_table <- mutation_freq %>%
    select(Mutation = resistance_mutation, `N (%)`) %>%
    left_join(by_tki, by = c("Mutation" = "resistance_mutation"))
} else {
  mutation_table <- mutation_freq %>%
    select(Mutation = resistance_mutation, `N (%)`)
}

ft <- flextable(mutation_table) %>%
  set_caption("Table: ABL1 Kinase Domain Mutation Frequency") %>%
  theme_vanilla() %>%
  autofit()

doc <- read_docx() %>%
  body_add_par("ABL1 Kinase Domain Resistance Mutations", style = "heading 1") %>%
  body_add_par(paste("Total patients with mutations:", nrow(resistance_df),
                     "of", nrow(df), sprintf("(%.1f%%)", nrow(resistance_df)/nrow(df)*100))) %>%
  body_add_flextable(ft)

print(doc, target = file.path(tables_dir, "CML_Resistance_Mutations.docx"))
cat("Saved: CML_Resistance_Mutations.docx\n")

# --- Resistance timeline plot (swimmer-style) ---
if (!all(is.na(resistance_df$time_to_resistance_months))) {
  timeline_df <- resistance_df %>%
    filter(!is.na(time_to_resistance_months)) %>%
    arrange(time_to_resistance_months) %>%
    mutate(patient_rank = factor(row_number()))

  p <- ggplot(timeline_df, aes(x = time_to_resistance_months, y = patient_rank)) +
    geom_segment(aes(x = 0, xend = time_to_resistance_months,
                     y = patient_rank, yend = patient_rank),
                 color = "grey70", linewidth = 2) +
    geom_point(aes(color = clinical_significance, shape = clinical_significance),
               size = 4) +
    geom_text(aes(label = resistance_mutation), hjust = -0.15, size = 2.5) +
    scale_color_manual(
      values = c(
        "T315I (pan-resistant)" = "#D32F2F",
        "Compound mutation" = "#FF6F00",
        "Clinically significant" = "#1976D2",
        "Other" = "#757575"
      ),
      name = "Mutation Type"
    ) +
    scale_shape_manual(
      values = c(
        "T315I (pan-resistant)" = 17,
        "Compound mutation" = 18,
        "Clinically significant" = 16,
        "Other" = 15
      ),
      name = "Mutation Type"
    ) +
    labs(
      title = "TKI Resistance Mutation Timeline",
      x = "Time from Treatment Start (months)",
      y = "Patient"
    ) +
    theme_minimal(base_size = 12) +
    theme(
      plot.title = element_text(hjust = 0.5, face = "bold"),
      axis.text.y = element_blank(),
      axis.ticks.y = element_blank(),
      panel.grid.major.y = element_blank()
    )

  ggsave(
    file.path(figures_dir, "CML_Resistance_Timeline.eps"),
    plot = p, device = "eps", width = 10, height = 6
  )
  cat("Saved: CML_Resistance_Timeline.eps\n")
} else {
  cat("Warning: Cannot generate timeline — missing date information\n")
}

cat("28_cml_resistance.R completed successfully\n")
