# Model Evaluation Report

Below are the generated evaluation plots for the order total model. Open this file's Markdown preview in VS Code to see the images inline.

## Regression Diagnostics

- Parity Plot: compares predicted vs. actual totals

![Parity](./order_total_parity.png)

- Residuals Distribution: error distribution (actual − predicted)

![Residuals](./order_total_residuals.png)

## Classification (High-Value Orders)

Using a high-value threshold derived from the 0.8 quantile of the target for evaluation-only framing.

- ROC Curve

![ROC](./order_total_roc.png)

- Precision–Recall Curve

![PR](./order_total_pr.png)

### Accuracy / Precision / F1 vs Threshold

This shows how metrics change as the score threshold varies.

![Metrics vs Threshold](./order_total_metrics_vs_threshold.png)

Best-threshold snapshot (bar chart):

![Best Metrics](./order_total_best_metrics.png)

### Confusion Matrix (Best Threshold)

![Confusion Matrix](./order_total_confusion_matrix.png)

## Summary JSON

A machine-readable summary with metrics and artifact paths:

- `evaluation_summary.json`
