# Clinical Validation Guide

Medical AI paper experimental sections must follow medical statistics and clinical research rigor.

## 1. Dataset Partitioning and Validation

-   **Internal Validation**: Training set, validation set, and internal test set.
-   **External Validation**: **The "gold standard" for Med-AI papers**. Must use data from different institutions, devices, or populations for independent testing to prove model generalization.
-   **Prospective vs. Retrospective**: 
    -   Retrospective studies (using historical data) are foundational.
    -   Prospective studies (real-time testing in clinical workflow) have higher evidence levels and are preferred by top journals (Nature Medicine, etc.).

## 2. Evaluation Metrics

In addition to traditional AI metrics, must include following medical metrics:

-   **Sensitivity (Recall) & Specificity**: Describe false negative and false positive rates.
-   **Positive/Negative Predictive Value (PPV/NPV)**: Describe clinical credibility of prediction results.
-   **AUC-ROC & AUC-PR**: Measure model performance at different thresholds.
-   **F1-Score**: Comprehensive performance under class imbalance (medical norm).
-   **Calibration Curve**: Measure consistency between predicted probabilities and actual occurrence rates.

## 3. Statistical Analysis

-   **Confidence Intervals (CI)**: All primary metrics (e.g., AUC 0.85 [95% CI: 0.82-0.88]) must include 95% confidence intervals.
-   **P-values**: Used to compare different models or performance against human doctors. Typically p < 0.05 considered statistically significant.
-   **Subgroup Analysis**: Check whether model performance is stable across different ages, genders, disease stages, or device types to identify potential algorithmic bias.

## 4. Comparison with Human Experts

-   **Reader Study**: Invite multiple clinicians (junior, intermediate, senior) to diagnose with and without AI assistance, comparing accuracy, time consumption, and consistency (Kappa coefficient).
-   **Ground Truth**: Clearly state Ground Truth source (e.g., pathological biopsy, consensus of multiple experts, follow-up results).
