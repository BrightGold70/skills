# Script: Sankey Diagram for Treatment Flow
# Purpose: Visualize patient flow between lines of therapy
# Output: .eps sankey diagram

library(ggplot2)
library(dplyr)
library(ggsankey)
library(tidyr)

# ==============================================================================
# COMMAND LINE ARGUMENTS
# ==============================================================================

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {
  cat("Usage: Rscript 16_sankey.R <data_file> <id_var> <line_vars> [output_dir]\n")
  cat("\nArguments:\n")
  cat("  data_file  : Path to CSV/Excel dataset\n")
  cat("  id_var     : Patient ID variable\n")
  cat("  line_vars  : Comma-separated line variables (e.g., LINE1,LINE2,LINE3)\n")
  cat("  output_dir : Output directory (default: Figures/)\n")
  cat("\nExample:\n")
  cat("  Rscript 16_sankey.R patient_data.csv PATIENT_ID LINE1_TRT,LINE2_TRT,LINE3_TRT\n")
  stop()
}

data_file <- args[1]
id_var <- args[2]
line_vars <- strsplit(args[3], ",")[[1]]
output_dir <- ifelse(length(args) >= 4, args[4], "Figures")

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
required_cols <- c(id_var, line_vars)
missing <- required_cols[!required_cols %in% names(df)]
if (length(missing) > 0) {
  stop(sprintf("Missing columns: %s", paste(missing, collapse = ", ")))
}

# ==============================================================================
# PREPARE SANKEY DATA
# ==============================================================================

# Select and rename columns
sankey_df <- df[, c(id_var, line_vars), drop = FALSE]
names(sankey_df)[1] <- "node"

# Create long format for transitions
# Each row represents a transition from one line to the next

transitions <- list()

for (i in 1:(length(line_vars) - 1)) {
  from_var <- line_vars[i]
  to_var <- line_vars[i + 1]
  
  # Create transition data
  trans_data <- sankey_df %>%
    select_(.dots = c("node", from_var, to_var)) %>%
    rename_(from = from_var, to = to_var) %>%
    filter(!is.na(from), !is.na(to), from != "", to != "") %>%
    mutate(
      from = paste0(from, "_L", i),
      to = paste0(to, "_L", i + 1)
    ) %>%
    group_by(from, to) %>%
    summarise(n = n(), .groups = "drop")
  
  transitions[[i]] <- trans_data
}

# Combine all transitions
all_transitions <- bind_rows(transitions)

# Also create entry point
entry_counts <- sankey_df %>%
  select_(line_vars[1]) %>%
  rename_(from = line_vars[1]) %>%
  filter(!is.na(from), from != "") %>%
  mutate(from = "Start") %>%
  group_by(from) %>%
  summarise(n = n(), .groups = "drop")

# Add entry to first line
first_line_counts <- sankey_df %>%
  select_(line_vars[1]) %>%
  rename_(to = line_vars[1]) %>%
  filter(!is.na(to), to != "") %>%
  mutate(to = paste0(to, "_L1")) %>%
  group_by(to) %>%
  summarise(n = n(), .groups = "drop")

entry_transitions <- cbind(
  from = rep("Start", nrow(first_line_counts)),
  to = first_line_counts$to,
  n = first_line_counts$n
)

# Combine with transitions
flow_data <- rbind(
  as.data.frame(entry_transitions),
  all_transitions
)

# ==============================================================================
# CREATE SANKEY PLOT
# ==============================================================================

cat("\nGenerating Sankey diagram...\n")

# If ggsankey not available, create manual version
if (!require("ggsankey", quietly = TRUE)) {
  cat("Installing ggsankey...\n")
  install.packages("ggsankey", repos = "https://cloud.r-project.org")
}

library(ggsankey)

# Prepare data in ggsankey format
sankey_long <- sankey_df %>%
  make_long(!!sym(line_vars[1]), !!sym(line_vars[2]), 
            labels = c("Line 1", "Line 2", "Line 3", "Line 4")[1:length(line_vars)])

# Create plot
p <- ggplot(sankey_long, aes(x = x, next_x = next_x, node = node, 
                            next_node = next_node, fill = factor(node))) +
  geom_sankey_flow(alpha = 0.5, color = "gray50") +
  geom_sankey_node(aes(x = x, label = node), width = 0.15) +
  theme_sankey() +
  labs(
    title = "Sankey Diagram: Treatment Line Transitions",
    subtitle = "Patient flow between lines of therapy",
    x = "",
    y = ""
  ) +
  theme(
    plot.title = element_text(hjust = 0.5, size = 14, face = "bold"),
    plot.subtitle = element_text(hjust = 0.5, size = 10),
    legend.position = "none"
  )

# Save as EPS
eps_file <- file.path(plots_dir, paste0("SankeyPlot_", format(Sys.Date(), "%Y%m%d"), ".eps"))

# Try EPS, fallback to PNG if issue
tryCatch({
  ggsave(filename = eps_file, plot = p, device = "eps", width = 14, height = 10)
}, error = function(e) {
  cat("EPS device issue, saving as PNG instead\n")
  eps_file <- gsub("\\.eps$", ".png", eps_file)
  ggsave(filename = eps_file, plot = p, width = 14, height = 10)
})

cat(sprintf("Sankey diagram saved to: %s\n", eps_file))

# ==============================================================================
# SUMMARY STATISTICS
# ==============================================================================

cat("\n========================================\n")
cat("TREATMENT FLOW SUMMARY\n")
cat("========================================\n\n")

# Count patients at each line
cat("Patients receiving each line of therapy:\n")
for (i in 1:length(line_vars)) {
  var <- line_vars[i]
  n_patients <- sum(!is.na(df[[var]]) & df[[var]] != "")
  cat(sprintf("  Line %d (%s): %d patients\n", i, var, n_patients))
}

# Most common transitions
cat("\nMost common transitions:\n")
if (nrow(all_transitions) > 0) {
  top_transitions <- all_transitions %>%
    arrange(desc(n)) %>%
    head(10)
  for (i in 1:nrow(top_transitions)) {
    t <- top_transitions[i, ]
    from_clean <- gsub("_L[0-9]$", "", t$from)
    to_clean <- gsub("_L[0-9]$", "", t$to)
    cat(sprintf("  %s -> %s: %d patients\n", from_clean, to_clean, t$n))
  }
}

cat("\nDone.\n")
