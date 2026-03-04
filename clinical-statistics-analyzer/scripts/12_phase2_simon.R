# Script: Simon Two-Stage Design for Phase 2
# Purpose: Optimal and Minimax designs for single-arm Phase 2 trials
# Output: Sample size tables for both designs

library(flextable)
library(officer)

# ==============================================================================
# COMMAND LINE ARGUMENTS
# ==============================================================================

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {
  cat("Usage: Rscript 12_phase2_simon.R <p0> <p1> [alpha] [power] [output_dir]\n")
  cat("\nArguments:\n")
  cat("  p0       : Null response rate (unacceptable)\n")
  cat("  p1       : Alternative response rate (acceptable)\n")
  cat("  alpha    : Type I error (default: 0.05)\n")
  cat("  power    : Statistical power (default: 0.80)\n")
  cat("  output_dir: Output directory (default: Tables/)\n")
  cat("\nExample:\n")
  cat("  # p0=0.10 (unacceptable), p1=0.30 (acceptable)\n")
  cat("  Rscript 12_phase2_simon.R 0.10 0.30\n")
  cat("  # With custom alpha/power\n")
  cat("  Rscript 12_phase2_simon.R 0.15 0.35 0.10 0.90\n")
  stop()
}

p0 <- as.numeric(args[1])  # Null response rate
p1 <- as.numeric(args[2])  # Alternative response rate
alpha <- ifelse(length(args) >= 3, as.numeric(args[3]), 0.05)
power <- ifelse(length(args) >= 4, as.numeric(args[4]), 0.80)
output_dir <- ifelse(length(args) >= 5, args[5], "Tables")

# Validate
if (p0 >= p1) {
  stop("p0 must be less than p1")
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
# SIMON TWO-STAGE DESIGN FUNCTIONS
# ==============================================================================

#' Calculate binomial probability
#' @param n Total patients
#' @param r Number of responses
#' @param p Response probability
#' @return Probability
binom_prob <- function(n, r, p) {
  choose(n, r) * p^r * (1 - p)^(n - r)
}

#' Calculate cumulative binomial probability
#' @param n Total patients
#' @param r Minimum responses
#' @param p Response probability
#' @return P(X <= r)
cum_binom <- function(n, r, p) {
  sum(sapply(0:r, function(k) binom_prob(n, k, p)))
}

#' Simon Optimal Design
#' @param p0 Null response rate
#' @param p1 Alternative response rate
#' @param alpha Type I error
#' @param power Power (1-beta)
#' @return List with n1, r1, n, r
simon_optimal <- function(p0, p1, alpha = 0.05, power = 0.80) {
  
  best <- NULL
  min_n <- Inf
  
  # Search over n1 (stage 1) and r1 (reject after stage 1)
  for (n1 in 1:30) {
    for (r1 in 0:n1) {
      # Skip if r1 >= n1 (would always continue)
      if (r1 >= n1) next
      
      # Type I error: P(reject | p0) = P(r1 > r1 | p0) + 
      #                            P(r1 <= r1, continue) * P(r > r2 | p0)
      
      # At stage 1: reject if r1 > r1 (not used, r1 is reject threshold)
      # Actually: if observed <= r1, continue
      
      # For Simon: reject H0 if:
      #   Stage 1: r1 > r1 (actually r1 responses triggers rejection of efficacy)
      #   OR Stage 2: after n total, r >= r2
      
      # Proper formulation:
      # r1 = number of responses to STOP early (reject efficacy)
      # If r1 responses in n1, reject (conclude ineffective)
      # Otherwise, continue to n total, reject if r >= r2
      
      # Probability of rejecting (type I):
      # P(reject at s1) + P(continue) * P(reject at s2)
      
      # At s1: reject if responses > r1 (actually means: if r1 >= r1 threshold, reject)
      # Let's use: r1 = max responses to "continue"
      
      # Re-formulate:
      # n1 = stage 1 sample
      # r1 = cutoff - if responses > r1 at stage 1, reject
      #     if responses <= r1, continue to stage 2
      # n = total sample
      # r = cutoff - if total responses >= r, reject
      
      for (n in (n1 + 1):60) {
        for (r in (r1 + 1):n) {
          
          # Type I error (under p0)
          # Reject if: reject at stage 1 OR reject at stage 2
          # Stage 1: P(responses > r1) under p0
          # Stage 2: P(continue to stage 2) * P(responses >= r | stage 2)
          
          # Reject at s1 if: r1 > r1 (more than r1 responses)
          # Actually standard: reject at s1 if responses >= r1+1
          # But Simon uses: reject at s1 if responses <= r1 (conclude inactive)
          
          # Let me use standard Simon: 
          # r1 = critical value at stage 1
          # r = critical value at stage 2
          
          # Correct formulation (Simon 1989):
          # Reject if: r1 >= r1 (actually <= for futility, but for efficacy rejection)
          
          # Let's use: n1 = patients at stage 1
          #           r1 = continue if responses <= r1, else reject (too good)
          #           n = total
          #           r = reject if total >= r
          
          # Actually standard: 
          # Stage 1: treat n1 patients
          # If responses <= r1, stop for futility (accept)
          # If responses > r1, continue to stage 2
          # Stage 2: treat additional n - n1 patients
          # If total responses >= r, reject (conclude effective)
          
          # Type I error (under p0):
          # P(futility stop at s1) + P(continue) * P(efficacy reject at s2)
          # = P(X <= r1) + P(X > r1) * P(Y >= r - r1)
          # where X ~ Bin(n1, p0), Y ~ Bin(n-n1, p0)
          
          # But the exact formula is more complex
          
          # Simplified using binomial:
          # P(reject | p0) = P(X <= r1) + P(X = r1+1) * P(Y >= r)
          # Actually: 
          # Stop for futility: X <= r1
          # Continue: X > r1
          # If continue: reject if X + Y >= r
          
          # Type I error:
          # P(stop early for futility | p0) + P(continue | p0) * P(reject at s2 | p0)
          # = P(X <= r1) + P(X > r1) * P(X + Y >= r)
          # where X ~ Bin(n1, p0), Y ~ Bin(n-n1, p0)
          
          # This is complex - use approximation
          # Exact: sum_{x=0}^{r1} binom_prob(n1, x, p0) +
          #         sum_{x=r1+1}^{n1} binom_prob(n1, x, p0) * 
          #         sum_{y=r-x}^{n-n1} binom_prob(n-n1, y, p0)
          
          type1 <- 0
          for (x in 0:r1) {
            type1 <- type1 + binom_prob(n1, x, p0)
          }
          for (x in (r1+1):n1) {
            p_x <- binom_prob(n1, x, p0)
            y_needed <- max(0, r - x)
            if (y_needed <= (n - n1)) {
              p_y <- 0
              for (y in y_needed:(n - n1)) {
                p_y <- p_y + binom_prob(n - n1, y, p0)
              }
              type1 <- type1 + p_x * p_y
            }
          }
          
          if (type1 > alpha) next
          
          # Power (under p1):
          # Similar calculation with p1 instead of p0
          power_calc <- 0
          for (x in 0:r1) {
            power_calc <- power_calc + binom_prob(n1, x, p1)
          }
          for (x in (r1+1):n1) {
            p_x <- binom_prob(n1, x, p1)
            y_needed <- max(0, r - x)
            if (y_needed <= (n - n1)) {
              p_y <- 0
              for (y in y_needed:(n - n1)) {
                p_y <- p_y + binom_prob(n - n1, y, p1)
              }
              power_calc <- power_calc + p_x * p_y
            }
          }
          
          if (power_calc >= power) {
            # Check if better than current best
            if (n < min_n) {
              min_n <- n
              best <- list(n1 = n1, r1 = r1, n = n, r = r, 
                         type1_error = type1, power = power_calc)
            }
          }
        }
      }
    }
  }
  
  return(best)
}

#' Simon Minimax Design
#' @param p0 Null response rate
#' @param p1 Alternative response rate  
#' @param alpha Type I error
#' @param power Power
#' @return List with design parameters
simon_minimax <- function(p0, p1, alpha = 0.05, power = 0.80) {
  
  best <- NULL
  min_expected_n <- Inf
  
  for (n1 in 1:30) {
    for (r1 in 0:n1) {
      
      if (r1 >= n1) next
      
      for (n in (n1 + 1):60) {
        for (r in (r1 + 1):n) {
          
          # Type I error calculation (same as optimal)
          type1 <- 0
          for (x in 0:r1) {
            type1 <- type1 + binom_prob(n1, x, p0)
          }
          for (x in (r1+1):n1) {
            p_x <- binom_prob(n1, x, p0)
            y_needed <- max(0, r - x)
            if (y_needed <= (n - n1)) {
              p_y <- 0
              for (y in y_needed:(n - n1)) {
                p_y <- p_y + binom_prob(n - n1, y, p0)
              }
              type1 <- type1 + p_x * p_y
            }
          }
          
          if (type1 > alpha) next
          
          # Power
          power_calc <- 0
          for (x in 0:r1) {
            power_calc <- power_calc + binom_prob(n1, x, p1)
          }
          for (x in (r1+1):n1) {
            p_x <- binom_prob(n1, x, p1)
            y_needed <- max(0, r - x)
            if (y_needed <= (n - n1)) {
              p_y <- 0
              for (y in y_needed:(n - n1)) {
                p_y <- p_y + binom_prob(n - n1, y, p1)
              }
              power_calc <- power_calc + p_x * p_y
            }
          }
          
          if (power_calc >= power) {
            # Expected sample size under p0
            # E[N] = n1 + (n - n1) * P(continue)
            # P(continue) = P(X > r1) under p0
            p_continue <- 0
            for (x in (r1+1):n1) {
              p_continue <- p_continue + binom_prob(n1, x, p0)
            }
            expected_n <- n1 + (n - n1) * p_continue
            
            # Minimax: minimize expected n under p0
            if (expected_n < min_expected_n) {
              min_expected_n <- expected_n
              best <- list(n1 = n1, r1 = r1, n = n, r = r,
                         type1_error = type1, power = power_calc,
                         expected_n = expected_n)
            }
          }
        }
      }
    }
  }
  
  return(best)
}

# ==============================================================================
# RUN SIMON DESIGNS
# ==============================================================================

cat("========================================\n")
cat("Simon Two-Stage Design for Phase 2\n")
cat("========================================\n\n")
cat(sprintf("Null response rate (p0): %.0f%%\n", p0 * 100))
cat(sprintf("Alternative response rate (p1): %.0f%%\n", p1 * 100))
cat(sprintf("Alpha (Type I error): %.2f\n", alpha))
cat(sprintf("Power (1-beta): %.2f\n\n", power))

cat("Searching for Optimal design...\n")
optimal <- simon_optimal(p0, p1, alpha, power)

cat("Searching for Minimax design...\n")
minimax <- simon_minimax(p0, p1, alpha, power)

# ==============================================================================
# DISPLAY RESULTS
# ==============================================================================

cat("\n========================================\n")
cat("RESULTS\n")
cat("========================================\n\n")

cat("OPTIMAL DESIGN (minimum total sample size):\n")
cat("-------------------------------------------\n")
if (!is.null(optimal)) {
  cat(sprintf("  Stage 1: n1 = %d patients\n", optimal$n1))
  cat(sprintf("  Stage 1 boundary: r1 = %d (reject if responses <= %d)\n", 
              optimal$r1, optimal$r1))
  cat(sprintf("  Total: n = %d patients\n", optimal$n))
  cat(sprintf("  Final boundary: r = %d (reject if total responses >= %d)\n",
              optimal$r, optimal$r))
  cat(sprintf("  Type I error: %.4f\n", optimal$type1_error))
  cat(sprintf("  Power: %.4f\n\n", optimal$power))
} else {
  cat("  No design found within search range\n\n")
}

cat("MINIMAX DESIGN (minimum expected sample size):\n")
cat("----------------------------------------------\n")
if (!is.null(minimax)) {
  cat(sprintf("  Stage 1: n1 = %d patients\n", minimax$n1))
  cat(sprintf("  Stage 1 boundary: r1 = %d (reject if responses <= %d)\n",
              minimax$r1, minimax$r1))
  cat(sprintf("  Total: n = %d patients\n", minimax$n))
  cat(sprintf("  Final boundary: r = %d (reject if total responses >= %d)\n",
              minimax$r, minimax$r))
  cat(sprintf("  Expected sample size (under p0): %.1f\n", minimax$expected_n))
  cat(sprintf("  Type I error: %.4f\n", minimax$type1_error))
  cat(sprintf("  Power: %.4f\n\n", minimax$power))
} else {
  cat("  No design found within search range\n\n")
}

# ==============================================================================
# CREATE OUTPUT TABLES
# ==============================================================================

# Design comparison table
if (!is.null(optimal) && !is.null(minimax)) {
  comp_df <- data.frame(
    Parameter = c("Design Type", "Stage 1 (n1)", "Continue if r >=", 
                   "Total (n)", "Reject if r >=", 
                   "Type I Error", "Power", "Expected N (p0)"),
    Optimal = c("Optimal", optimal$n1, optimal$r1, optimal$n, optimal$r,
                sprintf("%.4f", optimal$type1_error), sprintf("%.4f", optimal$power),
                "-"),
    Minimax = c("Minimax", minimax$n1, minimax$r1, minimax$n, minimax$r,
                 sprintf("%.4f", minimax$type1_error), sprintf("%.4f", minimax$power),
                 sprintf("%.1f", minimax$expected_n))
  )
  
  # Sensitivity analysis - vary p1
  cat("\nSensitivity Analysis (varying p1):\n")
  cat("===================================\n\n")
  
  p1_vals <- p1 + c(-0.10, -0.05, 0, 0.05, 0.10)
  p1_vals <- p1_vals[p1_vals > p0]
  
  sens_df <- data.frame(
    p1 = numeric(),
    Optimal_n = numeric(),
    Optimal_n1 = numeric(),
    Minimax_n = numeric(),
    Minimax_expected_n = numeric()
  )
  
  for (p in p1_vals) {
    opt <- simon_optimal(p0, p, alpha, power)
    minx <- simon_minimax(p0, p, alpha, power)
    
    sens_df <- rbind(sens_df, data.frame(
      p1 = sprintf("%.0f%%", p * 100),
      Optimal_n = ifelse(is.null(opt), "NA", opt$n),
      Optimal_n1 = ifelse(is.null(opt), "NA", opt$n1),
      Minimax_n = ifelse(is.null(minx), "NA", minx$n),
      Minimax_expected_n = ifelse(is.null(minx), "NA", sprintf("%.1f", minx$expected_n))
    ))
  }
  
  print(sens_df)
}

# Create Word document
ft_comp <- flextable(comp_df)
ft_comp <- theme_vanilla(ft_comp)
ft_comp <- bold(ft_comp, part = "header")

doc <- read_docx()
doc <- body_add_par(doc, "Simon Two-Stage Design Results", style = "Heading 1")
doc <- body_add_par(doc, sprintf("p0 = %.0f%% (null), p1 = %.0f%% (alternative)", 
                                  p0 * 100, p1 * 100), style = "Normal")
doc <- body_add_par(doc, sprintf("Alpha = %.2f, Power = %.0f%%", alpha, power * 100),
                    style = "Normal")
doc <- body_add_flextable(doc, value = ft_comp)

doc <- body_add_par(doc, "\nDesign Decision Rules:", style = "Heading 2")
doc <- body_add_par(doc, "1. Stage 1: Enroll n1 patients", style = "Normal")
doc <- body_add_par(doc, "2. If responses <= r1: Stop for futility (conclude inactive)", 
                    style = "Normal")
doc <- body_add_par(doc, "3. If responses > r1: Continue to Stage 2", style = "Normal")
doc <- body_add_par(doc, "4. Stage 2: Enroll additional patients to reach n total", 
                    style = "Normal")
doc <- body_add_par(doc, "5. If total responses >= r: Reject null (conclude effective)", 
                    style = "Normal")
doc <- body_add_par(doc, "6. Otherwise: Accept null (conclude inactive)", style = "Normal")

# Save
output_file <- file.path(tables_dir, paste0("Phase2_SimonTwoStage_", 
                                            format(Sys.Date(), "%Y%m%d"), ".docx"))
print(doc, target = output_file)

cat(sprintf("\nOutput saved to: %s\n", output_file))

# Save CSV
write.csv(comp_df, file.path(tables_dir, "Phase2_Simon_Comparison.csv"), 
           row.names = FALSE)

cat("Done.\n")
