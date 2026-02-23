#' Example Hematology Survival Analysis
#'
#' This script demonstrates a typical workflow for Hematology clinical data
#' using survival and cmprsk packages via rmcp.
#'
#' 1. Overall Survival (OS) using Kaplan-Meier
#' 2. Competing Risks (Relapse vs Non-Relapse Mortality)
#' 3. Hazard Ratios using Cox Regression

library(survival)
library(survminer)
library(cmprsk)

# --- 1. Load/Prepare Data ---
# Logic: Assume 'time' is follow-up in months, 'status' (0=censored, 1=death)
# Assume 'event_type' (0=censored, 1=relapse, 2=NRM)
# Assume 'risk_group' (Favorable, Intermediate, Adverse)

# mock_data <- read.csv("hematology_trial_data.csv")

# --- 2. Overall Survival (Kaplan-Meier) ---
# s_fit <- survfit(Surv(time, status) ~ risk_group, data = mock_data)

# ggsurvplot(s_fit,
#            pval = TRUE, conf.int = TRUE,
#            risk.table = TRUE,
#            title = "Overall Survival by Cytogenetic Risk Group",
#            xlab = "Months", ylab = "OS Probability")

# --- 3. Competing Risks (Cumulative Incidence) ---
# rel_fit <- cuminc(ftime = mock_data$time,
#                  fstatus = mock_data$event_type,
#                  group = mock_data$risk_group)

# plot(rel_fit, xlab = "Months", ylab = "Cumulative Incidence",
#      main = "Cumulative Incidence of Relapse (Event 1) and NRM (Event 2)")

# --- 4. Multivariate Cox Regression ---
# cox_model <- coxph(Surv(time, status) ~ risk_group + age + mrd_status,
#                    data = mock_data)
# summary(cox_model)

# --- 5. Export for Scientific-Visualization ---
# Swimmer plot data preparation
# waterfall_data <- mock_data[, c("patient_id", "blast_reduction_pct")]
# write.csv(waterfall_data, "waterfall_input.csv", row.names = FALSE)
