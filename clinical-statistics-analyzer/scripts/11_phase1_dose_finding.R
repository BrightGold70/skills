# Script: Phase 1 Dose-Finding Designs
# Purpose: 3+3 and CRM (Continual Reassessment Method) designs
# Output: MTD recommendation, dose escalation table

library(flextable)
library(officer)
library(dplyr)

# ==============================================================================
# COMMAND LINE ARGUMENTS
# ==============================================================================

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
  cat("Usage: Rscript 11_phase1_dose_finding.R <design> [target_toxicity] [max_cohorts] [output_dir]\n")
  cat("\nArguments:\n")
  cat("  design          : 3plus3 or CRM\n")
  cat("  target_toxicity : Target DLT rate (default: 0.33)\n")
  cat("  max_cohorts     : Maximum number of cohorts (default: 6)\n")
  cat("  output_dir      : Output directory (default: Tables/)\n")
  cat("\nExample:\n")
  cat("  Rscript 11_phase1_dose_finding.R 3plus3 0.33 6\n")
  cat("  Rscript 11_phase1_dose_finding.R CRM 0.25 8\n")
  stop()
}

design <- tolower(args[1])
target_toxicity <- ifelse(length(args) >= 2, as.numeric(args[2]), 0.33)
max_cohorts <- ifelse(length(args) >= 3, as.numeric(args[3]), 6)
output_dir <- ifelse(length(args) >= 4, args[4], "Tables")

if (!design %in% c("3plus3", "crm")) {
  stop("design must be '3plus3' or 'crm'")
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
# 3+3 DESIGN
# ==============================================================================

#' Classical 3+3 dose-finding algorithm
#' @param doses Vector of dose levels
#' @param dlt_rates True DLT rates for each dose (unknown in practice)
#' @param target Target toxicity rate
#' @return List with escalation history and MTD
design_3plus3 <- function(doses, dlt_rates = NULL, target = 0.33) {
  
  n_doses <- length(doses)
  current_dose <- 1
  cohorts <- list()
  cohort_num <- 1
  
  cat("\n========================================\n")
  cat("3+3 Dose-Finding Design\n")
  cat(sprintf("Target toxicity rate: %.0f%%\n", target * 100))
  cat("========================================\n\n")
  
  while (cohort_num <= max_cohorts && current_dose <= n_doses) {
    cat(sprintf("Cohort %d - Dose Level %d (%s)\n", 
                cohort_num, current_dose, doses[current_dose]))
    
    # Simulate patient outcomes if true rates provided
    if (!is.null(dlt_rates)) {
      n_patients <- 3
      dlt_events <- rbinom(1, n_patients, dlt_rates[current_dose])
    } else {
      cat("  Enter DLTs observed (0-3): ")
      dlt_events <- as.integer(readline())
    }
    
    # Record cohort
    cohorts[[cohort_num]] <- list(
      dose_level = current_dose,
      dose_name = doses[current_dose],
      n_patients = 3,
      dlt_events = dlt_events,
      decision = NA
    )
    
    # Decision rules
    if (dlt_events == 0) {
      # Escalate
      cohorts[[cohort_num]]$decision <- "Escalate"
      cat(sprintf("  DLTs: %d/3 - Escalate to next dose\n", dlt_events))
      current_dose <- min(current_dose + 1, n_doses)
      
    } else if (dlt_events == 1) {
      # Expand cohort (enroll 3 more)
      cat("  DLTs: 1/3 - Expand cohort to 6 patients\n")
      cohorts[[cohort_num]]$n_patients <- 6
      
      if (!is.null(dlt_rates)) {
        additional_dlts <- rbinom(1, 3, dlt_rates[current_dose])
        dlt_events <- dlt_events + additional_dlts
        cohorts[[cohort_num]]$dlt_events <- dlt_events
      } else {
        cat("  Enter additional DLTs in 3 patients: ")
        additional_dlts <- as.integer(readline())
        dlt_events <- dlt_events + additional_dlts
        cohorts[[cohort_num]]$dlt_events <- dlt_events
      }
      
      if (dlt_events <= 1) {
        cohorts[[cohort_num]]$decision <- "Escalate"
        cat(sprintf("  Total DLTs: %d/6 - Esclate\n", dlt_events))
        current_dose <- min(current_dose + 1, n_doses)
      } else {
        cohorts[[cohort_num]]$decision <- "Deescalate"
        cat(sprintf("  Total DLTs: %d/6 - Deescalate (MTD reached)\n", dlt_events))
        current_dose <- max(current_dose - 1, 1)
      }
      
    } else {
      # 2+ DLTs - Deescalate
      cohorts[[cohort_num]]$decision <- "Deescalate"
      cat(sprintf("  DLTs: %d/3 - Deescalate (MTD exceeded)\n", dlt_events))
      current_dose <- max(current_dose - 1, 1)
    }
    
    cohort_num <- cohort_num + 1
    
    # Check for MTD at lowest dose
    if (current_dose == 1 && dlt_events >= 2) {
      cat("\n*** MTD NOT ESTABLISHED - Trial may be terminated ***\n")
      break
    }
  }
  
  # Determine MTD
  mtd_dose <- current_dose
  
  # Count DLTs at each dose level
  dose_summary <- data.frame(
    Dose_Level = 1:n_doses,
    Dose = doses,
    N_Patients = sapply(cohorts, function(c) ifelse(c$dose_level == 1:n_doses[cohort_num-1], c$n_patients, 0)),
    DLTs = sapply(cohorts, function(c) ifelse(c$dose_level == 1:n_doses[cohort_num-1], c$dlt_events, 0))
  )
  
  return(list(
    design = "3+3",
    cohorts = cohorts,
    mtd_dose = mtd_dose,
    mtd_name = doses[mtd_dose],
    target = target,
    n_cohorts = cohort_num - 1
  ))
}

# ==============================================================================
# CRM DESIGN (Simplified)
# ==============================================================================

#' Continual Reassessment Method (CRM) - Bayesian design
#' @param doses Vector of dose levels
#' @param skeleton Prior DLT probabilities at each dose
#' @param target Target toxicity rate
#' @param cohort_size Patients per cohort
#' @param max_cohorts Maximum cohorts
#' @return MTD recommendation
design_crm <- function(doses, skeleton, target = 0.33, cohort_size = 1, max_cohorts = 6) {
  
  cat("\n========================================\n")
  cat("CRM (Continual Reassessment Method)\n")
  cat(sprintf("Target toxicity rate: %.0f%%\n", target * 100))
  cat("========================================\n\n")
  
  n_doses <- length(doses)
  
  # Initialize - start at dose level 1
  current_dose <- 1
  
  # Prior: use skeleton as initial estimates
  p_toxicity <- skeleton
  
  cohorts <- list()
  
  for (cohort_num in 1:max_cohorts) {
    cat(sprintf("Cohort %d - Dose Level %d (%s)\n", 
                cohort_num, current_dose, doses[current_dose]))
    
    # Simulate (in practice, this would be real patient data)
    cat("  Enter DLTs observed (0-1): ")
    dlt <- as.integer(readline())
    
    # Update using Bayesian logistic model (simplified)
    # In practice, use proper CRM with `dfens` or similar package
    # Here: simple isotonic regression update
    
    if (dlt == 1) {
      # Increase toxicity estimate for current and lower doses
      p_toxicity[current_dose] <- min(p_toxicity[current_dose] + 0.1, 1.0)
    } else {
      # Decrease toxicity estimate
      p_toxicity[current_dose] <- max(p_toxicity[current_dose] - 0.1, 0.0)
    }
    
    # Isotonic regression to ensure monotonicity
    p_toxicity <- isotonic.regression(p_toxicity)$fitted
    
    # Determine next dose - find dose closest to target
    dose_distances <- abs(p_toxicity - target)
    next_dose <- which.min(dose_distances)
    
    cohorts[[cohort_num]] <- list(
      dose_level = current_dose,
      dose_name = doses[current_dose],
      dlt = dlt,
      estimated_toxicity = p_toxicity[current_dose],
      next_dose = next_dose
    )
    
    cat(sprintf("  DLT: %d, Estimated toxicity: %.1f%%\n", 
                dlt, p_toxicity[current_dose] * 100))
    cat(sprintf("  Next dose: Level %d\n\n", next_dose))
    
    current_dose <- next_dose
    
    # Check stopping rule - if close to target for 3+ cohorts
    if (cohort_num >= 3) {
      recent_ests <- sapply(cohorts[(cohort_num-2):cohort_num], function(c) c$estimated_toxicity)
      if (all(abs(recent_ests - target) < 0.1)) {
        cat("*** Target toxicity achieved for 3 consecutive cohorts ***\n")
        cat("*** Consider stopping trial ***\n")
        break
      }
    }
  }
  
  # Final MTD = dose with toxicity closest to target
  final_mtd <- which.min(abs(p_toxicity - target))
  
  return(list(
    design = "CRM",
    cohorts = cohorts,
    mtd_dose = final_mtd,
    mtd_name = doses[final_mtd],
    toxicity_estimates = p_toxicity,
    target = target,
    n_cohorts = length(cohorts)
  ))
}

# Simple isotonic regression
isotonic.regression <- function(y) {
  n <- length(y)
  fitted <- y
  for (i in 2:n) {
    if (fitted[i] < fitted[i-1]) {
      # Find block
      j <- i
      while (j < n && fitted[j+1] < fitted[i-1]) {
        j <- j + 1
      }
      # Average block
      avg <- mean(y[i:j])
      fitted[i:j] <- avg
    }
  }
  list(fitted = fitted)
}

# ==============================================================================
# RUN SELECTED DESIGN
# ==============================================================================

# Define dose levels (example)
dose_levels <- c("Dose 1 (10mg)", "Dose 2 (20mg)", "Dose 3 (30mg)", 
                 "Dose 4 (40mg)", "Dose 5 (50mg)", "Dose 6 (60mg)")

if (design == "3plus3") {
  # Run 3+3 with simulated data (set seed for reproducibility)
  # In practice, replace with actual patient data
  set.seed(42)
  
  # True DLT rates (unknown in practice) - for demonstration
  true_dlt_rates <- c(0.05, 0.10, 0.20, 0.35, 0.50, 0.70)
  
  cat("Running 3+3 design with simulated outcomes...\n")
  result <- design_3plus3(dose_levels, true_dlt_rates, target_toxicity)
  
} else {
  # CRM design
  # Skeleton prior - initial estimates of DLT rates
  skeleton <- c(0.10, 0.20, 0.30, 0.40, 0.55, 0.70)
  
  cat("Running CRM design (enter patient data when prompted)...\n")
  cat("For simulation, enter 0 for no DLT, 1 for DLT\n\n")
  
  # Note: CRM requires real patient data; this is a template
  result <- design_crm(dose_levels, skeleton, target_toxicity)
}

# ==============================================================================
# OUTPUT RESULTS
# ==============================================================================

cat("\n========================================\n")
cat("FINAL RESULTS\n")
cat("========================================\n")
cat(sprintf("Design: %s\n", result$design))
cat(sprintf("Target toxicity: %.0f%%\n", result$target * 100))
cat(sprintf("Number of cohorts: %d\n", result$n_cohorts))
cat(sprintf("MTD: %s (Dose Level %d)\n", result$mtd_name, result$mtd_dose))

# Create summary table
summary_df <- data.frame(
  Parameter = c("Design", "Target Toxicity", "Number of Cohorts", 
                "MTD Dose Level", "MTD Name"),
  Value = c(result$design, 
            sprintf("%.0f%%", result$target * 100),
            as.character(result$n_cohorts),
            as.character(result$mtd_dose),
            result$mtd_name)
)

# Create cohort history table
cohort_history <- data.frame(
  Cohort = 1:length(result$cohorts),
  Dose_Level = sapply(result$cohorts, function(c) c$dose_level),
  Dose = sapply(result$cohorts, function(c) c$dose_name),
  N_Patients = sapply(result$cohorts, function(c) c$n_patients),
  DLTs = sapply(result$cohorts, function(c) c$dlt_events)
)

if (design == "crm") {
  cohort_history$DLTs <- sapply(result$cohorts, function(c) c$dlt)
  cohort_history$Est_Toxicity <- sapply(result$cohorts, function(c) 
    sprintf("%.1f%%", c$estimated_toxicity * 100))
}

# Create Word document
ft_summary <- flextable(summary_df)
ft_summary <- theme_vanilla(ft_summary)
ft_summary <- bold(ft_summary, part = "header")

ft_cohorts <- flextable(cohort_history)
ft_cohorts <- theme_vanilla(ft_cohorts)
ft_cohorts <- bold(ft_cohorts, part = "header")

doc <- read_docx()
doc <- body_add_par(doc, sprintf("Phase 1 Dose-Finding Results: %s", result$design), 
                    style = "Heading 1")
doc <- body_add_par(doc, sprintf("Target Toxicity: %.0f%%", result$target * 100))
doc <- body_add_flextable(doc, value = ft_summary)
doc <- body_add_par(doc, "\nDose Escalation History", style = "Heading 2")
doc <- body_add_flextable(doc, value = ft_cohorts)
doc <- body_add_par(doc, sprintf("\n>>> RECOMMENDED MTD: %s <<<\n", result$mtd_name),
                    style = "Normal")

# Save
output_file <- file.path(tables_dir, paste0("Phase1_DoseFinding_", design, "_", 
                                           format(Sys.Date(), "%Y%m%d"), ".docx"))
print(doc, target = output_file)

cat(sprintf("\nOutput saved to: %s\n", output_file))

# Save CSV backup
write.csv(cohort_history, file.path(tables_dir, paste0("Phase1_cohort_history_", design, ".csv")),
          row.names = FALSE)

cat("Done.\n")
