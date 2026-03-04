#!/usr/bin/env Rscript
# 26_cml_eln_milestones.R — ELN 2020 milestone response classification table
#
# Usage: Rscript 26_cml_eln_milestones.R <dataset> [--window 1.5]
#
# Outputs:
#   Tables/CML_ELN2020_Milestones.docx  — Milestone classification table
#   Figures/CML_ELN2020_Milestones_Heatmap.eps — Heatmap of response categories

suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(flextable)
  library(officer)
})

# --- Parse arguments ---
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: Rscript 26_cml_eln_milestones.R <dataset> [--window 1.5]")
}

dataset_path <- args[1]
window_months <- 1.5  # default ±1.5 months

# Parse optional --window argument
if ("--window" %in% args) {
  idx <- which(args == "--window")
  if (idx < length(args)) {
    window_months <- as.numeric(args[idx + 1])
  }
}

output_dir <- Sys.getenv("CSA_OUTPUT_DIR", ".")
tables_dir <- file.path(output_dir, "Tables")
figures_dir <- file.path(output_dir, "Figures")
dir.create(tables_dir, showWarnings = FALSE, recursive = TRUE)
dir.create(figures_dir, showWarnings = FALSE, recursive = TRUE)

# --- Load data ---
df <- read.csv(dataset_path, stringsAsFactors = FALSE)
cat("Loaded", nrow(df), "patients from", dataset_path, "\n")

# --- ELN 2020 Milestone Thresholds ---
# BCR-ABL % IS thresholds for optimal/warning/failure at each timepoint
eln_thresholds <- list(
  "3m"  = list(optimal = 10,   warning_upper = Inf,  failure = Inf,   col = "bcr_abl_3m"),
  "6m"  = list(optimal = 1,    warning_upper = 10,   failure = 10,    col = "bcr_abl_6m"),
  "12m" = list(optimal = 0.1,  warning_upper = 1,    failure = 1,     col = "bcr_abl_12m"),
  "18m" = list(optimal = 0.01, warning_upper = 0.1,  failure = 0.1,   col = "bcr_abl_18m")
)

# --- Classify patients at each timepoint ---
classify_milestone <- function(value, thresholds, timepoint) {
  if (is.na(value)) return("Not evaluable")

  if (timepoint == "3m") {
    # 3 months: Optimal = ≤10%, Warning = >10%, Failure = No CHR (approximated as very high)
    if (value <= thresholds$optimal) return("Optimal")
    if (value > 95) return("Failure")
    return("Warning")
  } else {
    # 6/12/18 months: Optimal = ≤threshold, Warning = between, Failure = >failure
    if (value <= thresholds$optimal) return("Optimal")
    if (value > thresholds$failure) return("Failure")
    return("Warning")
  }
}

results <- data.frame()

for (tp_name in names(eln_thresholds)) {
  tp <- eln_thresholds[[tp_name]]
  col <- tp$col

  if (!col %in% names(df)) {
    cat("Warning: Column", col, "not found, skipping timepoint", tp_name, "\n")
    next
  }

  classifications <- sapply(df[[col]], function(v) {
    classify_milestone(v, tp, tp_name)
  })

  tp_df <- data.frame(
    Patient_ID = df$Patient_ID,
    Treatment = if ("Treatment" %in% names(df)) df$Treatment else "All",
    Timepoint = tp_name,
    BCR_ABL = df[[col]],
    Classification = classifications,
    stringsAsFactors = FALSE
  )
  results <- rbind(results, tp_df)
}

# --- Summary table: N (%) per treatment arm, timepoint, category ---
summary_table <- results %>%
  filter(Classification != "Not evaluable") %>%
  group_by(Timepoint, Treatment, Classification) %>%
  summarise(N = n(), .groups = "drop") %>%
  group_by(Timepoint, Treatment) %>%
  mutate(
    Total = sum(N),
    Pct = sprintf("%.1f", N / Total * 100),
    Label = paste0(N, " (", Pct, "%)")
  ) %>%
  ungroup() %>%
  select(Timepoint, Treatment, Classification, Label) %>%
  pivot_wider(
    names_from = Classification,
    values_from = Label,
    values_fill = "0 (0.0%)"
  )

# Ensure column order
desired_cols <- c("Timepoint", "Treatment", "Optimal", "Warning", "Failure")
for (col in desired_cols) {
  if (!col %in% names(summary_table)) {
    summary_table[[col]] <- "0 (0.0%)"
  }
}
summary_table <- summary_table[, desired_cols]

# --- Generate flextable ---
ft <- flextable(summary_table) %>%
  set_header_labels(
    Timepoint = "Timepoint",
    Treatment = "Treatment",
    Optimal = "Optimal\nn (%)",
    Warning = "Warning\nn (%)",
    Failure = "Failure\nn (%)"
  ) %>%
  set_caption("Table: ELN 2020 Milestone Response Classification") %>%
  theme_vanilla() %>%
  autofit()

# Save .docx
doc <- read_docx() %>%
  body_add_par("ELN 2020 Milestone Response Classification", style = "heading 1") %>%
  body_add_par(paste("Window: ±", window_months, "months"), style = "Normal") %>%
  body_add_flextable(ft)

print(doc, target = file.path(tables_dir, "CML_ELN2020_Milestones.docx"))
cat("Saved: CML_ELN2020_Milestones.docx\n")

# --- Generate heatmap ---
heatmap_data <- results %>%
  filter(Classification != "Not evaluable") %>%
  mutate(
    Timepoint = factor(Timepoint, levels = c("3m", "6m", "12m", "18m")),
    Classification = factor(Classification, levels = c("Optimal", "Warning", "Failure"))
  ) %>%
  group_by(Timepoint, Classification) %>%
  summarise(N = n(), .groups = "drop") %>%
  group_by(Timepoint) %>%
  mutate(Pct = N / sum(N) * 100)

p <- ggplot(heatmap_data, aes(x = Timepoint, y = Classification, fill = Pct)) +
  geom_tile(color = "white", linewidth = 1) +
  geom_text(aes(label = sprintf("%.0f%%\n(n=%d)", Pct, N)), size = 3.5) +
  scale_fill_gradient2(
    low = "#2166AC", mid = "#F7F7F7", high = "#B2182B",
    midpoint = 50, name = "Patients (%)"
  ) +
  labs(
    title = "ELN 2020 Milestone Response Classification",
    x = "Assessment Timepoint",
    y = "Response Category"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    panel.grid = element_blank(),
    plot.title = element_text(hjust = 0.5, face = "bold")
  )

ggsave(
  file.path(figures_dir, "CML_ELN2020_Milestones_Heatmap.eps"),
  plot = p, device = "eps", width = 8, height = 5
)
cat("Saved: CML_ELN2020_Milestones_Heatmap.eps\n")

cat("26_cml_eln_milestones.R completed successfully\n")
