# Script: Swimmer Plot for Treatment Response
# Purpose: Patient-level visualization of treatment response over time
# Output: .eps swimmer plot with response milestones

library(ggplot2)
library(dplyr)
library(tidyr)

# ==============================================================================
# COMMAND LINE ARGUMENTS
# ==============================================================================

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
  cat("Usage: Rscript 15_swimmer_plot.R <data_file> <id_var> [time_var] [response_var] [treatment_var] [output_dir]\n")
  cat("\nArguments:\n")
  cat("  data_file      : Path to CSV/Excel dataset\n")
  cat("  id_var         : Patient ID variable\n")
  cat("  time_var       : Duration variable (optional, default: DURATION)\n")
  cat("  response_var   : Response variable (optional)\n")
  cat("  treatment_var  : Treatment variable (optional)\n")
  cat("  output_dir     : Output directory (default: Figures/)\n")
  cat("\nExample:\n")
  cat("  Rscript 15_swimmer_plot.R patient_data.csv PATIENT_ID OS_MONTHS RESPONSE Treatment\n")
  stop()
}

data_file <- args[1]
id_var <- args[2]
time_var <- ifelse(length(args) >= 3, args[3], "DURATION")
response_var <- ifelse(length(args) >= 4, args[4], NULL)
treatment_var <- ifelse(length(args) >= 5, args[5], NULL)
output_dir <- ifelse(length(args) >= 6, args[6], "Figures")

# ==============================================================================
# OUTPUT DIRECTORY
# ==============================================================================

output_base <- Sys.getenv("CSA_OUTPUT_DIR", "")
if (output_base == "") stop("CSA_OUTPUT_DIR not set. Export it first: export CSA_OUTPUT_DIR=/path/to/output")
plots_dir <- file.path(output_base, output_dir)
if (!dir.exists(plots_dir)) {
  dir.create(plots_dir, recursive = TRUE)
}

# ==============================================================================
# LOAD DATA
# ==============================================================================

cat("Loading data from:", data_file, "\n")

if (grepl("\\.xlsx$", data_file, ignore.case = TRUE)) {
  library(readxl)
  df <- read_excel(data_file)
} else {
  df <- read.csv(data_file, stringsAsFactors = FALSE)
}

cat("Data loaded:", nrow(df), "patients\n")

# Check required columns
if (!id_var %in% names(df)) {
  stop(sprintf("ID variable '%s' not found", id_var))
}
if (!time_var %in% names(df)) {
  stop(sprintf("Time variable '%s' not found", time_var))
}

# ==============================================================================
# PREPARE SWIMMER PLOT DATA
# ==============================================================================

# Convert to long format for plotting
plot_data <- df[, c(id_var, time_var, treatment_var, response_var), drop = FALSE]
names(plot_data)[1] <- "id"
names(plot_data)[2] <- "duration"

if (!is.null(treatment_var) && treatment_var %in% names(df)) {
  plot_data$treatment <- df[[treatment_var]]
}

if (!is.null(response_var) && response_var %in% names(df)) {
  plot_data$response <- df[[response_var]]
}

# Create response color mapping
response_colors <- c(
  "CR" = "#2ecc71",    # Complete Response - green
  "PR" = "#3498db",   # Partial Response - blue
  "SD" = "#f39c12",   # Stable Disease - orange
  "PD" = "#e74c3c",   # Progressive Disease - red
  "NE" = "#95a5a6"    # Not Evaluable - gray
)

# Sort by duration
plot_data <- plot_data[order(plot_data$duration, decreasing = FALSE), ]

# Create y-position (stacked)
plot_data$y_pos <- 1:nrow(plot_data)

# ==============================================================================
# CREATE SWIMMER PLOT
# ==============================================================================

cat("\nGenerating swimmer plot...\n")

# Base plot
p <- ggplot(plot_data, aes(x = duration, y = y_pos))

# Treatment duration bars
p <- p + geom_segment(aes(x = 0, xend = duration, y = y_pos, yend = y_pos),
                      size = 8, lineend = "round")

# Add response markers if available
if ("response" %in% names(plot_data)) {
  # Add response as colored circles at end
  p <- p + geom_point(aes(x = duration, y = y_pos, fill = response),
                     shape = 21, size = 6, color = "white", stroke = 1)
  
  # Color scale for responses
  p <- p + scale_fill_manual(values = response_colors, 
                              na.translate = FALSE)
}

# Treatment labels
if ("treatment" %in% names(plot_data)) {
  # Add treatment as text on bars
  p <- p + geom_text(aes(x = duration / 2, y = y_pos, label = treatment),
                    size = 3, color = "white", fontface = "bold")
}

# Formatting
p <- p + theme_minimal() +
  labs(
    title = "Swimmer Plot: Treatment Duration and Response",
    subtitle = ifelse("response" %in% names(plot_data),
                     "Each bar represents a patient; color indicates best response",
                     "Each bar represents a patient"),
    x = "Duration (months)",
    y = "Patient"
  ) +
  theme(
    plot.title = element_text(hjust = 0.5, size = 14, face = "bold"),
    plot.subtitle = element_text(hjust = 0.5, size = 10),
    axis.text.y = element_blank(),
    axis.ticks.y = element_blank(),
    panel.grid.major.y = element_blank(),
    panel.grid.minor.y = element_blank()
  ) +
  scale_x_continuous(expand = c(0, 0))

# Add legend for response if available
if ("response" %in% names(plot_data)) {
  p <- p + guides(fill = guide_legend(title = "Best Response"))
}

# Save as EPS
eps_file <- file.path(plots_dir, paste0("SwimmerPlot_", format(Sys.Date(), "%Y%m%d"), ".eps"))
ggsave(filename = eps_file, plot = p, device = "eps", width = 12, height = max(8, nrow(plot_data) * 0.15))

cat(sprintf("Swimmer plot saved to: %s\n", eps_file))

# ==============================================================================
# SUMMARY STATISTICS
# ==============================================================================

cat("\n========================================\n")
cat("SUMMARY STATISTICS\n")
cat("========================================\n\n")

cat(sprintf("Total patients: %d\n", nrow(plot_data)))
cat(sprintf("Median duration: %.1f months\n", median(plot_data$duration, na.rm = TRUE)))
cat(sprintf("Range: %.1f - %.1f months\n", 
            min(plot_data$duration, na.rm = TRUE), 
            max(plot_data$duration, na.rm = TRUE)))

if ("treatment" %in% names(plot_data)) {
  cat("\nBy Treatment:\n")
  treatment_summary <- plot_data %>%
    group_by(treatment) %>%
    summarise(
      n = n(),
      median_duration = median(duration, na.rm = TRUE),
      mean_duration = mean(duration, na.rm = TRUE)
    )
  print(treatment_summary)
}

if ("response" %in% names(plot_data)) {
  cat("\nBy Response:\n")
  response_summary <- plot_data %>%
    group_by(response) %>%
    summarise(
      n = n(),
      pct = n() / nrow(plot_data) * 100,
      median_duration = median(duration, na.rm = TRUE)
    )
  print(response_summary)
}

cat("\nDone.\n")
