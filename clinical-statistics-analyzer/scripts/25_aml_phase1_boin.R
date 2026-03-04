#!/usr/bin/env Rscript

# BOIN (Bayesian Optimal Interval) Phase 1 Dose-Finding for AML
# Implementation based on Liu & Yuan, 2015

suppressPackageStartupMessages({
  library(flextable)
  library(officer)
  library(ggplot2)
  library(dplyr)
})

args <- commandArgs(trailingOnly = TRUE)
target_dlt <- if (length(args) >= 1) as.numeric(args[1]) else 0.25
n_doses    <- if (length(args) >= 2) as.integer(args[2]) else 6
cohort_size<- if (length(args) >= 3) as.integer(args[3]) else 3
n_trials   <- if (length(args) >= 4) as.integer(args[4]) else 1000

# Constants & Paths
out_dir <- Sys.getenv("CSA_OUTPUT_DIR", "")
if (out_dir == "") stop("CSA_OUTPUT_DIR not set. Export it first: export CSA_OUTPUT_DIR=/path/to/output")
dir.create(file.path(out_dir, "Tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(out_dir, "Figures"), recursive = TRUE, showWarnings = FALSE)

phi <- target_dlt
p1 <- 0.6 * phi
p2 <- 1.4 * phi

# 1. Calculate BOIN Boundaries
lambda_e <- log((1 - p1) / (1 - phi)) / log((phi * (1 - p1)) / (p1 * (1 - phi)))
lambda_d <- log((1 - phi) / (1 - p2)) / log((p2 * (1 - phi)) / (phi * (1 - p2)))

max_n <- min(30, cohort_size * 10)
n_seq <- 1:max_n
escalate_bound <- floor(lambda_e * n_seq)
deescalate_bound <- ceiling(lambda_d * n_seq)

# Overdose control elimination boundary: posterior prob(true toxicity > phi) > 0.95
overdose_bound <- sapply(n_seq, function(n) {
  for (y in 0:n) {
    if ((1 - pbeta(phi, 1 + y, 1 + n - y)) > 0.95) return(y)
  }
  return(NA)
})

# Correct bounds: deescalate should be > escalate
deescalate_bound <- pmax(deescalate_bound, escalate_bound + 2)

decision_df <- data.frame(
  Number_of_Patients = n_seq,
  Escalate_if_DLT_le = escalate_bound,
  Deescalate_if_DLT_ge = deescalate_bound,
  Eliminate_if_DLT_ge = overdose_bound
)

# Keep only rows where patients are multiples of cohort_size
table_df <- decision_df %>% filter(Number_of_Patients %% cohort_size == 0)

# Write decision table
ft_decision <- flextable(table_df) %>%
  set_caption(caption = paste("BOIN Decision Boundaries (Target DLT =", target_dlt, ")")) %>%
  autofit()

doc <- read_docx() %>%
  body_add_flextable(value = ft_decision)
print(doc, target = file.path(out_dir, "Tables", "BOIN_Decision_Boundaries.docx"))


# 2. Simulation Setup
pava <- function(y, w) {
  n <- length(y)
  if (n <= 1) return(y)
  val <- y
  weight <- w
  blocks_start <- 1:n
  blocks_end <- 1:n
  
  while (TRUE) {
    is_violating <- diff(val) < 0
    if (!any(is_violating)) break
    i <- which(is_violating)[1]
    new_w <- weight[i] + weight[i+1]
    new_v <- (val[i]*weight[i] + val[i+1]*weight[i+1]) / new_w
    val[i] <- new_v
    weight[i] <- new_w
    blocks_end[i] <- blocks_end[i+1]
    val <- val[-(i+1)]
    weight <- weight[-(i+1)]
    blocks_start <- blocks_start[-(i+1)]
    blocks_end <- blocks_end[-(i+1)]
  }
  res <- rep(0, n)
  for (k in seq_along(val)) res[blocks_start[k]:blocks_end[k]] <- val[k]
  return(res)
}

simulate_trial <- function(true_pi, max_n_trial = 30) {
  n_pts <- rep(0, n_doses)
  n_dlt <- rep(0, n_doses)
  eliminated <- rep(FALSE, n_doses)
  current_dose <- 1
  total_pts <- 0
  
  while (total_pts < max_n_trial) {
    if (eliminated[1]) break
    
    # Treat cohort
    n_pts[current_dose] <- n_pts[current_dose] + cohort_size
    y <- rbinom(1, cohort_size, true_pi[current_dose])
    n_dlt[current_dose] <- n_dlt[current_dose] + y
    total_pts <- total_pts + cohort_size
    
    curr_n <- n_pts[current_dose]
    curr_y <- n_dlt[current_dose]
    
    # Overdose control
    if (!is.na(overdose_bound[curr_n]) && curr_y >= overdose_bound[curr_n]) {
      eliminated[current_dose:n_doses] <- TRUE
      if (current_dose > 1 && !eliminated[current_dose - 1]) {
        current_dose <- current_dose - 1
        next
      } else {
        break
      }
    }
    
    # BOIN decision
    p_hat <- curr_y / curr_n
    if (p_hat <= lambda_e) {
      if (current_dose < n_doses && !eliminated[current_dose + 1]) {
        current_dose <- current_dose + 1
      }
    } else if (p_hat >= lambda_d) {
      if (current_dose > 1) {
        current_dose <- current_dose - 1
      }
    }
  }
  
  # Select MTD
  valid_doses <- which(n_pts > 0 & !eliminated)
  if (length(valid_doses) == 0) {
    mtd <- 0
  } else {
    y_valid <- n_dlt[valid_doses] / n_pts[valid_doses]
    w_valid <- n_pts[valid_doses]
    p_iso <- pava(y_valid, w_valid)
    
    # Minimize distance to target
    diffs <- abs(p_iso - target_dlt)
    min_diff <- min(diffs)
    candidates <- valid_doses[diffs == min_diff]
    mtd <- max(candidates) # Break tie in favor of higher dose
  }
  
  return(list(mtd = mtd, n_pts = n_pts, n_dlt = n_dlt))
}

# Define Scenarios
scenarios <- list(
  Scenario_1 = seq(0.05, by=0.10, length.out=n_doses),
  Scenario_2 = seq(0.15, by=0.10, length.out=n_doses),
  Scenario_3 = seq(0.25, by=0.10, length.out=n_doses),
  Scenario_4 = seq(0.35, by=0.10, length.out=n_doses)
)
# Constrain probabilities
scenarios <- lapply(scenarios, function(x) pmin(x, 0.99))

results_list <- list()

for (s_name in names(scenarios)) {
  true_pi <- scenarios[[s_name]]
  mtd_sel <- rep(0, n_doses + 1)
  pts_alloc <- rep(0, n_doses)
  dlt_alloc <- rep(0, n_doses)
  
  for (i in 1:n_trials) {
    sim <- simulate_trial(true_pi, max_n_trial = cohort_size * 10)
    if (sim$mtd == 0) {
      mtd_sel[n_doses + 1] <- mtd_sel[n_doses + 1] + 1
    } else {
      mtd_sel[sim$mtd] <- mtd_sel[sim$mtd] + 1
    }
    pts_alloc <- pts_alloc + sim$n_pts
    dlt_alloc <- dlt_alloc + sim$n_dlt
  }
  
  res_df <- data.frame(
    Scenario = s_name,
    Dose_Level = c(paste("Dose", 1:n_doses), "None"),
    True_DLT_Rate = c(true_pi, NA),
    MTD_Selection_Prob = mtd_sel / n_trials,
    Avg_Patients = c(pts_alloc / n_trials, NA),
    Avg_DLTs = c(dlt_alloc / n_trials, NA)
  )
  results_list[[s_name]] <- res_df
}

final_results <- bind_rows(results_list)

# Write Operating Characteristics
ft_oc <- flextable(final_results) %>%
  set_caption(caption = paste("BOIN Operating Characteristics (", n_trials, "trials)")) %>%
  colformat_double(digits = 3) %>%
  autofit()

doc2 <- read_docx() %>%
  body_add_flextable(value = ft_oc)
print(doc2, target = file.path(out_dir, "Tables", "BOIN_Operating_Characteristics.docx"))

# 3. Plot Isotoxicity Curve (Selection Probabilities)
plot_df <- final_results %>% filter(Dose_Level != "None")

p <- ggplot(plot_df, aes(x = True_DLT_Rate, y = MTD_Selection_Prob)) +
  geom_point(aes(color = Scenario), size = 3) +
  geom_smooth(method = "loess", se = FALSE, color = "blue", linewidth = 1) +
  geom_vline(xintercept = target_dlt, linetype = "dashed", color = "red") +
  theme_minimal() +
  labs(title = "BOIN Selection Probability Profile",
       x = "True DLT Rate", y = "Probability of Selection as MTD") +
  theme(legend.position = "bottom")

setEPS()
postscript(file.path(out_dir, "Figures", "BOIN_Isotoxicity_Curve.eps"), width = 8, height = 6)
print(p)
invisible(dev.off())

cat(paste0("BOIN analysis complete. Outputs saved to ", out_dir, "/\n"))
