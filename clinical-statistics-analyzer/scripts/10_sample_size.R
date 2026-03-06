# Script: Sample Size Calculation for Clinical Trials
# Purpose: Calculate sample sizes for Phase 1-3 clinical trials
# Supports: binary endpoints, continuous endpoints, time-to-event (survival)
# Uses: pwr package for power calculations

library(pwr)
library(flextable)
library(officer)
library(dplyr)

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

# ==============================================================================
# COMMAND LINE ARGUMENTS
# ==============================================================================

args <- commandArgs(trailingOnly = TRUE)

# Parse arguments
arg_names <- c("endpoint_type", "alpha", "power", "effect_size", "allocation_ratio", "output_file")
defaults <- list("binary", 0.05, 0.80, NULL, 1, NULL)

if (length(args) == 0) {
  cat("Usage: Rscript 10_sample_size.R <endpoint_type> [alpha] [power] [effect_size] [allocation_ratio] [output_dir]\n")
  cat("\nArguments:\n")
  cat("  endpoint_type   : binary, continuous, or survival\n")
  cat("  alpha          : significance level (default: 0.05)\n")
  cat("  power          : statistical power (default: 0.80)\n")
  cat("  effect_size    : effect size (OR for binary, Cohen's d for continuous, HR for survival)\n")
  cat("  allocation_ratio: allocation ratio treatment:control (default: 1)\n")
  cat("  output_dir     : output directory (default: Tables/)\n")
  cat("\nExamples:\n")
  cat("  # Binary endpoint (response rate 30% vs 50%)\n")
  cat("  Rscript 10_sample_size.R binary 0.05 0.80 0.50\n")
  cat("  # Continuous endpoint (effect size 0.5)\n")
  cat("  Rscript 10_sample_size.R continuous 0.05 0.80 0.5\n")
  cat("  # Survival endpoint (HR = 0.7, 50% events required)\n")
  cat("  Rscript 10_sample_size.R survival 0.05 0.80 0.7\n")
  stop()
}

# Parse or use defaults
endpoint_type <- ifelse(length(args) >= 1, args[1], defaults[[1]])
alpha <- ifelse(length(args) >= 2, as.numeric(args[2]), defaults[[2]])
power <- ifelse(length(args) >= 3, as.numeric(args[3]), defaults[[3]])
effect_size <- ifelse(length(args) >= 4, as.numeric(args[4]), defaults[[4]])
allocation_ratio <- ifelse(length(args) >= 5, as.numeric(args[5]), defaults[[6]])
output_dir <- ifelse(length(args) >= 6, args[6], "Tables")

# Validate inputs
if (is.na(alpha) || alpha <= 0 || alpha >= 1) {
  stop("Alpha must be between 0 and 1")
}
if (is.na(power) || power <= 0 || power >= 1) {
  stop("Power must be between 0 and 1")
}
if (is.na(allocation_ratio) || allocation_ratio <= 0) {
  stop("Allocation ratio must be positive")
}

# ==============================================================================
# OUTPUT DIRECTORY
# ==============================================================================

output_base <- Sys.getenv("CSA_OUTPUT_DIR", "")
if (output_base == "") stop("CSA_OUTPUT_DIR not set. Export it first: export CSA_OUTPUT_DIR=/path/to/output")
tables_dir <- file.path(output_base, output_dir)
if (!dir.exists(tables_dir)) {
  dir.create(tables_dir, recursive = TRUE)
}

# ==============================================================================
# SAMPLE SIZE CALCULATION FUNCTIONS
# ==============================================================================

#' Calculate sample size for binary endpoint (two proportions)
#' @param p1 Response rate in treatment group
#' @param p2 Response rate in control group
#' @param alpha Significance level
#' @param power Statistical power
#' @param ratio Allocation ratio (n1/n2)
#' @return Sample size per group and total
calc_binary <- function(p1, p2, alpha = 0.05, power = 0.80, ratio = 1) {
  # Convert proportions to odds ratio
  or <- (p1 * (1 - p2)) / (p2 * (1 - p1))
  
  # Use pwr.2p.test for two proportions
  result <- pwr.2p.test(h = ES.h(p1, p2), 
                         sig.level = alpha, 
                         power = power, 
                         alternative = "two.sided")
  
  n1 <- ceiling(result$n)
  n2 <- ceiling(n1 / ratio)
  
  list(
    method = "Two-proportion chi-square test",
    p1 = p1,
    p2 = p2,
    OR = or,
    n_per_group = n1,
    n_total = n1 + n2,
    n1 = n1,
    n2 = n2,
    alpha = alpha,
    power = power
  )
}

#' Calculate sample size for continuous endpoint (two means)
#' @param d Cohen's d effect size
#' @param alpha Significance level
#' @param power Statistical power
#' @param ratio Allocation ratio
calc_continuous <- function(d, alpha = 0.05, power = 0.80, ratio = 1) {
  result <- pwr.t.test(d = d, 
                       sig.level = alpha, 
                       power = power, 
                       type = "two.sample",
                       alternative = "two.sided")
  
  n1 <- ceiling(result$n)
  n2 <- ceiling(n1 / ratio)
  
  list(
    method = "Two-sample t-test",
    effect_size_d = d,
    n_per_group = n1,
    n_total = n1 + n2,
    n1 = n1,
    n2 = n2,
    alpha = alpha,
    power = power
  )
}

#' Calculate sample size for survival endpoint (log-rank test)
#' @param hr Hazard ratio
#' @param alpha Significance level
#' @param power Statistical power
#' @param total_time Total follow-up time
#' @param fraction_events Fraction of subjects expected to have event
calc_survival <- function(hr, alpha = 0.05, power = 0.80, 
                          total_time = 24, fraction_events = 0.5) {
  # Using Schoenfeld formula for survival analysis
  # n = (Z_alpha + Z_beta)^2 * (1 + 1/r) / (log(HR))^2
  
  z_alpha <- qnorm(1 - alpha/2)
  z_beta <- qnorm(power)
  
  # Total events required
  d_events <- ((z_alpha + z_beta)^2 * (1 + 1)^2) / (log(hr)^2)
  d_events <- ceiling(d_events)
  
  # Total sample size based on expected events
  n_total <- ceiling(d_events / fraction_events)
  
  # Per group (assuming 1:1 allocation)
  n_per_group <- ceiling(n_total / 2)
  
  list(
    method = "Log-rank test (Schoenfeld formula)",
    hazard_ratio = hr,
    events_required = d_events,
    n_per_group = n_per_group,
    n_total = n_total,
    alpha = alpha,
    power = power,
    expected_events = fraction_events
  )
}

# ==============================================================================
# MAIN CALCULATION
# ==============================================================================

cat("========================================\n")
cat("Sample Size Calculation for Clinical Trial\n")
cat("========================================\n\n")

results <- list()

switch(endpoint_type,
       "binary" = {
         if (is.null(effect_size)) {
           cat("For binary endpoint, effect_size = OR (Odds Ratio)\n")
           cat("Example: OR = 2.0 means treatment has twice the odds of response\n")
           # Default example: 30% vs 50% response
           effect_size <- 0.50 / 0.30
           cat(sprintf("Using default OR = %.2f (30%% vs 50%% response)\n", effect_size))
         }
         p1 <- 0.3  # Treatment response rate
         p2 <- p1 / effect_size / (1 - p1 + p1 / effect_size)  # Derive p2 from OR
         results$main <- calc_binary(p1, p2, alpha, power, allocation_ratio)
         
         # Sensitivity analysis
         cat("\nSensitivity Analysis:\n")
         cat("-------------------\n")
         or_vals <- c(1.5, 2.0, 2.5, 3.0, 3.5, 4.0)
         sens_results <- data.frame(
           OR = or_vals,
           n_per_group = sapply(or_vals, function(or) {
             p1_t <- p1
             p2_t <- p1_t / or / (1 - p1_t + p1_t / or)
             r <- tryCatch(calc_binary(p1_t, p2_t, alpha, power, allocation_ratio)$n_per_group,
                          error = function(e) NA)
             r
           }),
           n_total = sapply(or_vals, function(or) {
             p1_t <- p1
             p2_t <- p1_t / or / (1 - p1_t + p1_t / or)
             r <- tryCatch(calc_binary(p1_t, p2_t, alpha, power, allocation_ratio)$n_total,
                          error = function(e) NA)
             r
           })
         )
         results$sensitivity <- sens_results
         cat(sprintf("OR = %.1f: n = %d per group, %d total\n", 
                    sens_results$OR[2], sens_results$n_per_group[2], sens_results$n_total[2]))
       },
       
       "continuous" = {
         if (is.null(effect_size)) {
           effect_size <- 0.5
           cat("Using default Cohen's d = 0.5 (medium effect)\n")
         }
         results$main <- calc_continuous(effect_size, alpha, power, allocation_ratio)
         
         # Sensitivity analysis
         cat("\nSensitivity Analysis:\n")
         cat("-------------------\n")
         d_vals <- c(0.2, 0.3, 0.4, 0.5, 0.6, 0.8)
         sens_results <- data.frame(
           Cohen_d = d_vals,
           n_per_group = sapply(d_vals, function(d) {
             calc_continuous(d, alpha, power, allocation_ratio)$n_per_group
           }),
           n_total = sapply(d_vals, function(d) {
             calc_continuous(d, alpha, power, allocation_ratio)$n_total
           })
         )
         results$sensitivity <- sens_results
         cat(sprintf("d = %.1f: n = %d per group, %d total\n", 
                    sens_results$Cohen_d[4], sens_results$n_per_group[4], sens_results$n_total[4]))
       },
       
       "survival" = {
         if (is.null(effect_size)) {
           effect_size <- 0.7
           cat("Using default HR = 0.7 (30%% reduction in hazard)\n")
         }
         results$main <- calc_survival(effect_size, alpha, power)
         
         # Sensitivity analysis
         cat("\nSensitivity Analysis:\n")
         cat("-------------------\n")
         hr_vals <- c(0.5, 0.6, 0.7, 0.8, 0.9)
         sens_results <- data.frame(
           HR = hr_vals,
           events_required = sapply(hr_vals, function(hr) {
             calc_survival(hr, alpha, power)$events_required
           }),
           n_per_group = sapply(hr_vals, function(hr) {
             calc_survival(hr, alpha, power)$n_per_group
           }),
           n_total = sapply(hr_vals, function(hr) {
             calc_survival(hr, alpha, power)$n_total
           })
         )
         results$sensitivity <- sens_results
         cat(sprintf("HR = %.1f: n = %d per group, %d total\n", 
                    sens_results$HR[3], sens_results$n_per_group[3], sens_results$n_total[3]))
       },
       
       {
         stop("Invalid endpoint_type. Use: binary, continuous, or survival")
       }
)

# ==============================================================================
# DISPLAY MAIN RESULTS
# ==============================================================================

cat("\n========================================\n")
cat("MAIN RESULTS\n")
cat("========================================\n")
cat(sprintf("Method: %s\n", results$main$method))
cat(sprintf("Significance level (alpha): %.2f\n", results$main$alpha))
cat(sprintf("Power: %.2f\n", results$main$power))
cat(sprintf("Allocation ratio: %.1f:1\n", allocation_ratio))
cat("\n")

if (endpoint_type == "binary") {
  cat(sprintf("Treatment response rate: %.1f%%\n", results$main$p1 * 100))
  cat(sprintf("Control response rate: %.1f%%\n", results$main$p2 * 100))
  cat(sprintf("Odds Ratio: %.2f\n", results$main$OR))
} else if (endpoint_type == "continuous") {
  cat(sprintf("Cohen's d effect size: %.2f\n", results$main$effect_size_d))
} else {
  cat(sprintf("Hazard Ratio: %.2f\n", results$main$hazard_ratio))
}

cat(sprintf("\n>>> Required sample size: %d per group, %d total <<<\n", 
            results$main$n_per_group, results$main$n_total))

# Add dropout adjustment (10%)
dropout_rate <- 0.10
n_adjusted <- ceiling(results$main$n_total / (1 - dropout_rate))
cat(sprintf("\nWith %.0f%% dropout adjustment: %d total subjects\n", 
            dropout_rate * 100, n_adjusted))

# ==============================================================================
# CREATE OUTPUT TABLE
# ==============================================================================

# Main results table
main_df <- data.frame(
  Parameter = c("Method", "Endpoint Type", "Alpha", "Power", 
                "Allocation Ratio", "Effect Size",
                "N per Group", "N Total", "N Total (10% dropout)"),
  Value = c(results$main$method, 
            endpoint_type,
            as.character(results$main$alpha),
            as.character(results$main$power),
            as.character(allocation_ratio),
            if(endpoint_type == "binary") sprintf("OR = %.2f", results$main$OR)
            else if(endpoint_type == "continuous") sprintf("d = %.2f", results$main$effect_size_d)
            else sprintf("HR = %.2f", results$main$hazard_ratio),
            as.character(results$main$n_per_group),
            as.character(results$main$n_total),
            as.character(n_adjusted))
)

# Sensitivity analysis table
sens_df <- results$sensitivity

# Create flextable
ft_main <- flextable(main_df)
ft_main <- theme_vanilla(ft_main)
ft_main <- bold(ft_main, part = "header")
ft_main <- colformat_double(ft_main, digits = 2)

# Save to Word
doc <- read_docx()
doc <- body_add_par(doc, "Sample Size Calculation Results", style = "Heading 1")
doc <- body_add_flextable(doc, value = ft_main)

# Add sensitivity analysis
doc <- body_add_par(doc, "\nSensitivity Analysis", style = "Heading 2")
ft_sens <- flextable(sens_df)
ft_sens <- theme_vanilla(ft_sens)
ft_sens <- bold(ft_sens, part = "header")
doc <- body_add_flextable(doc, value = ft_sens)

# Add interpretation
doc <- body_add_par(doc, "\nInterpretation", style = "Heading 2")
interpretation <- sprintf(
  "For a %s endpoint with alpha = %.2f and power = %.2f, ",
  endpoint_type, alpha, power)
if (endpoint_type == "binary") {
  interpretation <- paste0(interpretation, 
    sprintf("detecting an odds ratio of %.2f (%.0f%% vs %.0f%% response) ",
            results$main$OR, results$main$p1*100, results$main$p2*100),
    sprintf("requires %d subjects per arm (%d total). ", 
            results$main$n_per_group, results$main$n_total),
    sprintf("Accounting for 10%% dropout, %d subjects are needed.", n_adjusted))
} else if (endpoint_type == "continuous") {
  interpretation <- paste0(interpretation,
    sprintf("detecting a Cohen's d effect size of %.2f ", effect_size),
    sprintf("requires %d subjects per arm (%d total). ", 
            results$main$n_per_group, results$main$n_total),
    sprintf("Accounting for 10%% dropout, %d subjects are needed.", n_adjusted))
} else {
  interpretation <- paste0(interpretation,
    sprintf("detecting a hazard ratio of %.2f ", effect_size),
    sprintf("requires %d events and %d subjects per arm (%d total). ", 
            results$main$events_required, results$main$n_per_group, results$main$n_total),
    sprintf("Accounting for 10%% dropout, %d subjects are needed.", n_adjusted))
}
doc <- body_add_par(doc, interpretation)

# Save document
output_file <- file.path(tables_dir, paste0("SampleSize_", endpoint_type, "_", 
                                             format(Sys.Date(), "%Y%m%d"), ".docx"))
print(doc, target = output_file)

cat("\n========================================\n")
cat(sprintf("Output saved to: %s\n", output_file))
cat("========================================\n")

# Save CSV backup
write.csv(main_df, file.path(tables_dir, paste0("SampleSize_", endpoint_type, "_main.csv")), 
          row.names = FALSE)
write.csv(sens_df, file.path(tables_dir, paste0("SampleSize_", endpoint_type, "_sensitivity.csv")), 
          row.names = FALSE)

cat("Done.\n")

# ── Emit stats sidecar ────────────────────────────────────────────────────────
tryCatch({
  stats_list <- list(
    n_total          = results$main$n_total,
    n_adjusted       = n_adjusted,
    alpha            = results$main$alpha,
    power            = results$main$power,
    endpoint_type    = endpoint_type
  )
  if (endpoint_type == "binary") {
    stats_list$effect_size_or <- round(results$main$OR, 2)
    stats_list$p1             <- round(results$main$p1, 3)
    stats_list$p2             <- round(results$main$p2, 3)
  } else if (endpoint_type == "continuous") {
    stats_list$effect_size_d  <- round(results$main$effect_size_d, 2)
  } else if (endpoint_type == "survival") {
    stats_list$hazard_ratio    <- round(results$main$hazard_ratio, 2)
    stats_list$events_required <- results$main$events_required
  }
  write_stats_json(
    key_statistics = stats_list,
    analysis_notes = list(
      dropout_adjustment = "10%",
      formula            = switch(endpoint_type,
        binary   = "Two-proportion chi-square (pwr.2p.test)",
        continuous = "Two-sample t-test (pwr.t.test)",
        survival = "Log-rank / Schoenfeld formula"
      )
    )
  )
}, error = function(e) message("[write_stats_json] Skipped (error): ", e$message))
