# Script: Survival and Competing Risks Analysis
# Purpose: Kaplan-Meier plots, Cox proportional hazards models, and Competing Risks (Cumulative Incidence)

library(survival)
library(survminer)
library(cmprsk)

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

args <- commandArgs(trailingOnly = TRUE)
# NEW: Modified to accept optional 4th argument [disease]
if(length(args) < 3) {
  stop("Usage: Rscript 04_survival.R <dataset_path> <time_var> <status_var> [disease]")
}

input_data_path <- args[1]
time_var <- args[2]
status_var <- args[3] # Usually 0 = censor, 1 = event (or multiple codes for competing risks)

# NEW: Parse optional --disease argument
disease <- ""
if (length(args) >= 4) {
  if (grepl("--disease=", args[4])) {
    disease <- tolower(sub("--disease=", "", args[4]))
  } else if (args[4] == "--disease" && length(args) >= 5) {
    disease <- tolower(args[5])
  } else if (!grepl("^--", args[4])) {
    disease <- tolower(args[4])
  }
}

output_dir <- Sys.getenv("CSA_OUTPUT_DIR", "")
if (output_dir == "") stop("CSA_OUTPUT_DIR not set. Export it first: export CSA_OUTPUT_DIR=/path/to/output")
plots_dir <- file.path(output_dir, "Figures")
# NEW: Defined tables_dir to fix missing variable bug from original script
tables_dir <- file.path(output_dir, "Tables")

if(!dir.exists(plots_dir)) dir.create(plots_dir, recursive = TRUE)
if(!dir.exists(tables_dir)) dir.create(tables_dir, recursive = TRUE)

df <- read.csv(input_data_path)

# NEW: Helper function to run cox.zph(), print/warn, and save results
run_cox_zph <- function(cox_model, model_name) {
  tryCatch({
    zph_res <- cox.zph(cox_model)
    cat("\n--- Proportional Hazards Assumption Test (Schoenfeld Residuals) ---\n")
    print(zph_res)
    
    # Warn if any p < 0.05
    p_vals <- zph_res$table[, "p"]
    if(any(p_vals < 0.05, na.rm = TRUE)) {
      warning(paste("Proportional hazards assumption violated (p < 0.05) in model:", model_name))
    }
    
    # Save result as CSV
    zph_df <- as.data.frame(zph_res$table)
    zph_df$variable <- rownames(zph_df)
    write.csv(zph_df, file.path(tables_dir, paste0("CoxZPH_", model_name, ".csv")), row.names=FALSE)
    cat("Saved cox.zph results to:", file.path(tables_dir, paste0("CoxZPH_", model_name, ".csv")), "\n\n")
    
  }, error = function(e) {
    cat("Error running cox.zph() for", model_name, ":", e$message, "\n")
  })
}

# NEW: Disease-specific logic and GRFS competing risks detection
is_grfs <- grepl("grfs|GRFS", time_var) | (disease == "hct" && "grfs_event" %in% names(df))

if (is_grfs && "grfs_competing" %in% names(df)) {
  cat("GRFS endpoint detected with competing risks. Using Fine-Gray analysis (not KM).\n")
  
  grfs_time <- if (disease == "hct" && "grfs_time" %in% names(df)) "grfs_time" else time_var
  grfs_status <- "grfs_competing"
  
  if ("Treatment" %in% names(df)) {
    # Cumulative incidence plot
    ci_fit <- cuminc(ftime = df[[grfs_time]], fstatus = df[[grfs_status]], group = df$Treatment)
    
    eps_file_cr <- file.path(plots_dir, paste0("Cumulative_Incidence_GRFS_", grfs_time, ".eps"))
    postscript(file = eps_file_cr, width = 8, height = 6)
    plot(ci_fit, xlab = "Time", ylab = "Cumulative Incidence", main = paste("GRFS Competing Risks:", grfs_time))
    dev.off()
    cat("GRFS Cumulative Incidence plot saved to:", eps_file_cr, "\n")
    
    # Fine-Gray model using crr
    df_cc <- df[!is.na(df[[grfs_time]]) & !is.na(df[[grfs_status]]) & !is.na(df$Treatment), ]
    if(length(unique(df_cc$Treatment)) > 1) {
      cov1 <- model.matrix(~ Treatment, data = df_cc)[, -1, drop = FALSE]
      crr_fit <- crr(ftime = df_cc[[grfs_time]], fstatus = df_cc[[grfs_status]], cov1 = cov1, failcode = 1, cencode = 0)
      cat("\n--- Fine-Gray Competing Risks Regression (CRR) ---\n")
      print(summary(crr_fit))
      
      crr_summary <- as.data.frame(summary(crr_fit)$coef)
      write.csv(crr_summary, file.path(tables_dir, paste0("FineGray_GRFS_", grfs_time, ".csv")), row.names=TRUE)
    } else {
      cat("Not enough 'Treatment' groups for Fine-Gray regression.\n")
    }
  } else {
    cat("No 'Treatment' column found. Skipping GRFS Fine-Gray comparison.\n")
  }
} else {
  
  if (is_grfs) {
    # NEW: For GRFS as composite, treat all non-censored as event=1 if no true competing risk column exists
    cat("GRFS detected without a true competing risk column. Treating all non-censored as event=1.\n")
    df[[status_var]] <- ifelse(df[[status_var]] != 0, 1, 0)
  }

  # --- Survival Analysis (Kaplan-Meier) ---
  formula_km <- paste("Surv(", time_var, ",", status_var, ") ~ Treatment")

  if("Treatment" %in% names(df)) {
    fit <- survfit(as.formula(formula_km), data = df)
    
    km_plot <- ggsurvplot(fit, data = df, pval = TRUE, conf.int = TRUE,
                          risk.table = TRUE,
                          ggtheme = theme_minimal(),
                          title = paste("Kaplan-Meier Curve:", time_var))
    
    eps_file <- file.path(plots_dir, paste0("KM_Plot_", time_var, ".eps"))
    ggsave(filename = eps_file, print(km_plot), device = "eps", width = 8, height = 6)
    cat("Kaplan-Meier plot saved to:", eps_file, "\n")
    
    # --- Cox Proportional Hazards Model ---
    cox_model <- coxph(as.formula(formula_km), data = df)
    print(summary(cox_model))
    
    # NEW: Run proportional hazards assumption test
    run_cox_zph(cox_model, time_var)
    
    # Save standard Cox model results
    library(broom)
    cox_summary <- tidy(cox_model, conf.int = TRUE, exponentiate = TRUE)
    write.csv(cox_summary, file.path(tables_dir, paste0("Cox_", time_var, "_Analysis.csv")), row.names=FALSE)
  } else {
    cat("No 'Treatment' column found. Skipping KM comparison.\n")
  }
}

# --- Time-Dependent Cox Regression (e.g., for HCT) ---
# To address immortal time bias, we evaluate HCT as a time-varying covariate if the data provides it.
if("time_to_hct" %in% names(df) && "hct_status" %in% names(df) && "id" %in% names(df)) {
  cat("Performing time-dependent Cox regression for HCT...\n")
  
  # Split data into start/stop format using tmerge
  tdata <- tmerge(data1 = df, data2 = df, id = id,
                  event = event(df[[time_var]], df[[status_var]]),
                  hct = tdc(time_to_hct))
  
  td_formula <- "Surv(tstart, tstop, event) ~ hct"
  if("Treatment" %in% names(df)) {
    td_formula <- paste(td_formula, "+ Treatment")
  }
  
  td_cox <- coxph(as.formula(td_formula), data = tdata)
  print(summary(td_cox))
  
  # NEW: Run proportional hazards assumption test
  run_cox_zph(td_cox, paste0("TimeDependent_HCT_", time_var))
  
  library(broom)
  td_summary <- tidy(td_cox, conf.int = TRUE, exponentiate = TRUE)
  write.csv(td_summary, file.path(tables_dir, paste0("TimeDependent_Cox_HCT_", time_var, ".csv")), row.names=FALSE)
} else {
  cat("Time-dependent HCT variables ('time_to_hct', 'hct_status', 'id') not found. Skipping time-varying Cox.\n")
}

# --- Competing Risks Analysis (Cumulative Incidence) ---
# Assuming status_var has codes: 0=censor, 1=Event of Interest, 2=Competing Event
# NEW: Do not re-run competing risks if we already ran it in the GRFS section above
if (!(is_grfs && "grfs_competing" %in% names(df))) {
  unique_statuses <- unique(df[[status_var]])
  if(length(unique_statuses) > 2) {
    cat("More than 2 status codes detected. Assuming competing risks setup.\n")
    
    if("Treatment" %in% names(df)){
      ci_fit <- cuminc(ftime = df[[time_var]], fstatus = df[[status_var]], group = df$Treatment)
      
      eps_file_cr <- file.path(plots_dir, paste0("Cumulative_Incidence_", time_var, ".eps"))
      postscript(file = eps_file_cr, width = 8, height = 6)
      plot(ci_fit, xlab = "Time", ylab = "Cumulative Incidence", main = paste("Competing Risks:", time_var))
      dev.off()
      cat("Cumulative Incidence plot saved to:", eps_file_cr, "\n")
    }
  }
}

cat("Survival analysis script completed.\n")

# ── Emit stats sidecar ────────────────────────────────────────────────────────
tryCatch({
  stats_list <- list(n_total = nrow(df))
  if (exists("fit")) {
    sm <- summary(fit)$table
    if (!is.null(sm) && "median" %in% colnames(sm)) {
      med_val <- round(as.numeric(sm[1, "median"]), 1)
      lo_val  <- round(as.numeric(sm[1, "0.95LCL"]), 1)
      hi_val  <- round(as.numeric(sm[1, "0.95UCL"]), 1)
      stats_list[[paste0(time_var, "_median_months")]] <- list(value=med_val, unit="months", ci_lower=lo_val, ci_upper=hi_val)
      if (grepl("^(os|OS|overall|Overall)", time_var)) {
        stats_list$os_median_months <- list(value=med_val, unit="months", ci_lower=lo_val, ci_upper=hi_val)
      } else if (grepl("^(pfs|PFS|prog|relapse)", time_var)) {
        stats_list$pfs_median_months <- list(value=med_val, unit="months", ci_lower=lo_val, ci_upper=hi_val)
      }
    }
  }
  if (exists("cox_summary") && is.data.frame(cox_summary) && nrow(cox_summary) > 0) {
    hr_key <- if (grepl("^(pfs|PFS)", time_var)) "pfs_hr" else "os_hr"
    stats_list[[hr_key]] <- list(
      value    = round(cox_summary$estimate[1], 2),
      ci_lower = round(cox_summary$conf.low[1], 2),
      ci_upper = round(cox_summary$conf.high[1], 2),
      p_value  = round(cox_summary$p.value[1], 3)
    )
  }
  write_stats_json(
    key_statistics = stats_list,
    analysis_notes = list(
      survival_model = "Kaplan-Meier; Cox proportional hazards regression",
      ph_assumption  = "cox.zph tested (see CoxZPH CSV output)"
    )
  )
}, error = function(e) message("[write_stats_json] Skipped (error): ", e$message))
