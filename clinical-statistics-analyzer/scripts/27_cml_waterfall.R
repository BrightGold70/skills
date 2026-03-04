#!/usr/bin/env Rscript
# 27_cml_waterfall.R — BCR-ABL response depth waterfall plot
#
# Usage: Rscript 27_cml_waterfall.R <dataset> [--timepoint 12]
#
# Outputs:
#   Figures/CML_Waterfall_BCR_ABL.eps — Waterfall plot
#   Tables/CML_Response_Depth.docx    — Summary table of response categories

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(flextable)
  library(officer)
})

# --- Parse arguments ---
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: Rscript 27_cml_waterfall.R <dataset> [--timepoint 12]")
}

dataset_path <- args[1]
timepoint <- 12  # default: 12 months

if ("--timepoint" %in% args) {
  idx <- which(args == "--timepoint")
  if (idx < length(args)) {
    timepoint <- as.numeric(args[idx + 1])
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

# --- Determine timepoint column ---
tp_col <- paste0("bcr_abl_", timepoint, "m")
if (!tp_col %in% names(df)) {
  stop("Column '", tp_col, "' not found in dataset")
}
if (!"bcr_abl_baseline" %in% names(df)) {
  stop("Column 'bcr_abl_baseline' required")
}

# --- Calculate log10 reduction ---
waterfall_df <- df %>%
  filter(!is.na(bcr_abl_baseline) & !is.na(.data[[tp_col]])) %>%
  filter(bcr_abl_baseline > 0 & .data[[tp_col]] > 0) %>%
  mutate(
    log10_reduction = log10(.data[[tp_col]] / bcr_abl_baseline),
    response_category = case_when(
      log10_reduction <= -4.5 ~ "MR4.5",
      log10_reduction <= -4.0 ~ "MR4",
      log10_reduction <= -3.0 ~ "MMR",
      log10_reduction <= -2.0 ~ "Partial",
      TRUE ~ "Minimal/None"
    )
  ) %>%
  arrange(log10_reduction) %>%
  mutate(
    rank = row_number(),
    response_category = factor(
      response_category,
      levels = c("MR4.5", "MR4", "MMR", "Partial", "Minimal/None")
    )
  )

cat("Calculated log10 reduction for", nrow(waterfall_df), "patients\n")

# --- Waterfall plot ---
treatment_col <- if ("Treatment" %in% names(waterfall_df)) "Treatment" else NULL

p <- ggplot(waterfall_df, aes(x = rank, y = log10_reduction))

if (!is.null(treatment_col)) {
  p <- p + geom_bar(aes(fill = Treatment), stat = "identity", width = 0.8)
} else {
  p <- p + geom_bar(aes(fill = response_category), stat = "identity", width = 0.8)
}

p <- p +
  # Threshold lines
  geom_hline(yintercept = -3, linetype = "dashed", color = "#E69F00", linewidth = 0.6) +
  geom_hline(yintercept = -4, linetype = "dashed", color = "#56B4E9", linewidth = 0.6) +
  geom_hline(yintercept = -4.5, linetype = "dashed", color = "#009E73", linewidth = 0.6) +
  # Threshold labels
  annotate("text", x = nrow(waterfall_df) + 0.5, y = -3, label = "MMR",
           hjust = 0, vjust = -0.5, size = 3, color = "#E69F00") +
  annotate("text", x = nrow(waterfall_df) + 0.5, y = -4, label = "MR4",
           hjust = 0, vjust = -0.5, size = 3, color = "#56B4E9") +
  annotate("text", x = nrow(waterfall_df) + 0.5, y = -4.5, label = "MR4.5",
           hjust = 0, vjust = -0.5, size = 3, color = "#009E73") +
  scale_y_continuous(
    breaks = seq(-6, 2, by = 1),
    limits = c(min(waterfall_df$log10_reduction, -5) - 0.5,
               max(waterfall_df$log10_reduction, 0) + 0.5)
  ) +
  labs(
    title = paste0("BCR-ABL Response Depth at ", timepoint, " Months"),
    subtitle = "Log10 reduction from baseline (lower = deeper response)",
    x = "Patients (ranked by response depth)",
    y = "Log10(BCR-ABL ratio vs baseline)"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(hjust = 0.5, face = "bold"),
    plot.subtitle = element_text(hjust = 0.5),
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    panel.grid.major.x = element_blank()
  )

ggsave(
  file.path(figures_dir, "CML_Waterfall_BCR_ABL.eps"),
  plot = p, device = "eps", width = 10, height = 6
)
cat("Saved: CML_Waterfall_BCR_ABL.eps\n")

# --- Response depth summary table ---
summary_df <- waterfall_df %>%
  group_by(response_category) %>%
  summarise(N = n(), .groups = "drop") %>%
  mutate(
    Pct = sprintf("%.1f", N / sum(N) * 100),
    `N (%)` = paste0(N, " (", Pct, "%)")
  ) %>%
  select(Category = response_category, `N (%)`)

# Add by treatment arm if available
if (!is.null(treatment_col)) {
  by_treatment <- waterfall_df %>%
    group_by(Treatment, response_category) %>%
    summarise(N = n(), .groups = "drop") %>%
    group_by(Treatment) %>%
    mutate(
      Pct = sprintf("%.1f", N / sum(N) * 100),
      Label = paste0(N, " (", Pct, "%)")
    ) %>%
    select(response_category, Treatment, Label) %>%
    pivot_wider(names_from = Treatment, values_from = Label, values_fill = "0 (0.0%)")

  summary_df <- summary_df %>%
    left_join(by_treatment, by = c("Category" = "response_category"))
}

ft <- flextable(summary_df) %>%
  set_caption(paste0("Table: BCR-ABL Response Depth at ", timepoint, " Months")) %>%
  theme_vanilla() %>%
  autofit()

doc <- read_docx() %>%
  body_add_par(paste0("BCR-ABL Response Depth at ", timepoint, " Months"), style = "heading 1") %>%
  body_add_flextable(ft)

print(doc, target = file.path(tables_dir, "CML_Response_Depth.docx"))
cat("Saved: CML_Response_Depth.docx\n")

cat("27_cml_waterfall.R completed successfully\n")
