import os
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, roc_auc_score, precision_recall_curve, roc_curve, f1_score, average_precision_score, confusion_matrix
from sklearn.model_selection import train_test_split
import joblib
import matplotlib.pyplot as plt


def get_engine():
    url = os.getenv("DATABASE_URL", "postgresql://postgres:Sam12kumar%40@localhost:5432/ETL_DB")
    return create_engine(url)


def load_order_features(engine, limit=None, delivered_only=True):
    where = "WHERE fo.order_status = 'delivered'" if delivered_only else ""
    lim = f"LIMIT {int(limit)}" if limit else ""
    #
    # Features:
    # - num_items: count(order_items)
    # - avg_item_price: avg(price per item)
    # - total_items_price: sum(price)
    # - freight_value: from fact_orders
    # Target:
    # - order_total: from fact_orders
    #
    q = f"""
        SELECT
            fo.order_id,
            COUNT(oi.product_id)                                        AS num_items,
            AVG(oi.price_cents) / 100.0                                 AS avg_item_price,
            SUM(oi.price_cents) / 100.0                                 AS total_items_price,
            COALESCE(SUM(oi.freight_value_cents) / 100.0, 0)            AS freight_value,
            COALESCE(fo.order_total_cents, 0) / 100.0                   AS order_total
        FROM fact_orders fo
        JOIN fact_order_items oi ON oi.order_id = fo.order_id
        {where}
        GROUP BY fo.order_id, fo.order_total_cents
        {lim}
    """
    with engine.connect() as c:
        df = pd.read_sql(text(q), c)
    # Drop rows with missing target just in case
    df = df.dropna(subset=["order_total"]) 
    return df


def ensure_reports_dir():
    reports = Path(__file__).resolve().parent / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    return reports


def load_or_train_model(X, y, model_path: Path):
    if model_path.exists():
        return joblib.load(model_path)
    # Fallback quick model if not found
    rf = RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    return rf


def regression_diagnostics(y_true, y_pred, out_dir: Path, prefix="order_total"):
    # Compute RMSE compatible with older sklearn versions
    mse = mean_squared_error(y_true, y_pred)
    rmse = float(np.sqrt(mse))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    # Parity plot
    plt.figure(figsize=(6, 6))
    lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
    plt.scatter(y_true, y_pred, alpha=0.3, s=10)
    plt.plot(lims, lims, 'r--', linewidth=1)
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.title(f"Parity Plot — RMSE: {rmse:.2f}, MAE: {mae:.2f}, R²: {r2:.3f}")
    plt.tight_layout()
    plt.savefig(out_dir / f"{prefix}_parity.png", dpi=150)
    plt.close()

    # Residuals histogram
    residuals = y_true - y_pred
    plt.figure(figsize=(6, 4))
    plt.hist(residuals, bins=50, alpha=0.8)
    plt.xlabel("Residual (Actual - Predicted)")
    plt.ylabel("Count")
    plt.title("Residuals Distribution")
    plt.tight_layout()
    plt.savefig(out_dir / f"{prefix}_residuals.png", dpi=150)
    plt.close()

    return {"rmse": rmse, "mae": mae, "r2": r2}


def classification_curves(y_true_reg, y_score_reg, out_dir: Path, prefix="order_total", threshold=None, quantile=0.8):
    # Convert regression target to classification: high-value order
    if threshold is None:
        threshold = float(np.quantile(y_true_reg, quantile))
    y_true = (y_true_reg >= threshold).astype(int)

    # Use regression predictions as scores
    y_score = y_score_reg

    # ROC
    fpr, tpr, _ = roc_curve(y_true, y_score)
    roc_auc = roc_auc_score(y_true, y_score)
    plt.figure(figsize=(6, 6))
    plt.plot(fpr, tpr, label=f"ROC AUC = {roc_auc:.3f}")
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve (High-Value Classification)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(out_dir / f"{prefix}_roc.png", dpi=150)
    plt.close()

    # Precision-Recall
    precision, recall, pr_thresholds = precision_recall_curve(y_true, y_score)
    ap = average_precision_score(y_true, y_score)
    plt.figure(figsize=(6, 6))
    plt.plot(recall, precision, label=f"AP = {ap:.3f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve (High-Value Classification)")
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(out_dir / f"{prefix}_pr.png", dpi=150)
    plt.close()

    # Choose operating point: maximize F1 by thresholding scores at best cut
    best_f1 = 0.0
    best_thr = None
    for thr in np.linspace(y_score.min(), y_score.max(), num=101):
        y_pred = (y_score >= thr).astype(int)
        f1 = f1_score(y_true, y_pred)
        if f1 > best_f1:
            best_f1 = f1
            best_thr = thr

    # Compute metrics at best_thr
    y_pred_best = (y_score >= best_thr).astype(int)
    f1_best = f1_score(y_true, y_pred_best)

    return {
        "threshold": threshold,
        "roc_auc": float(roc_auc),
        "average_precision": float(ap),
        "best_operating_point": {"score_threshold": float(best_thr), "f1": float(f1_best)},
    }


def plot_metrics_vs_threshold(y_true_reg, y_score_reg, out_dir: Path, prefix="order_total", quantile=0.8):
    # Classification target derived from regression target
    thr_val = float(np.quantile(y_true_reg, quantile))
    y_true = (y_true_reg >= thr_val).astype(int)
    y_score = y_score_reg

    thr_min, thr_max = float(y_score.min()), float(y_score.max())
    thresholds = np.linspace(thr_min, thr_max, num=101)

    acc_list, prec_list, f1_list = [], [], []
    best = {"threshold": None, "accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    for t in thresholds:
        y_pred = (y_score >= t).astype(int)
        tp = int(((y_pred == 1) & (y_true == 1)).sum())
        tn = int(((y_pred == 0) & (y_true == 0)).sum())
        fp = int(((y_pred == 1) & (y_true == 0)).sum())
        fn = int(((y_pred == 0) & (y_true == 1)).sum())
        total = tp + tn + fp + fn

        accuracy = (tp + tn) / total if total else 0.0
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

        acc_list.append(accuracy)
        prec_list.append(precision)
        f1_list.append(f1)

        if f1 > best["f1"]:
            best = {"threshold": float(t), "accuracy": float(accuracy), "precision": float(precision), "recall": float(recall), "f1": float(f1)}

    # Line plot for Accuracy / Precision / F1 vs threshold
    plt.figure(figsize=(7, 5))
    plt.plot(thresholds, acc_list, label="Accuracy")
    plt.plot(thresholds, prec_list, label="Precision")
    plt.plot(thresholds, f1_list, label="F1")
    plt.xlabel("Score Threshold")
    plt.ylabel("Metric Value")
    plt.title("Accuracy / Precision / F1 vs Threshold")
    plt.legend()
    plt.tight_layout()
    metrics_vs_thr_path = out_dir / f"{prefix}_metrics_vs_threshold.png"
    plt.savefig(metrics_vs_thr_path, dpi=150)
    plt.close()

    # Bar chart for best threshold metrics
    plt.figure(figsize=(6, 4))
    names = ["Accuracy", "Precision", "F1"]
    vals = [best["accuracy"], best["precision"], best["f1"]]
    plt.bar(names, vals, color=["#4c78a8", "#f58518", "#54a24b"])
    plt.ylim(0, 1)
    plt.title(f"Best Metrics at Threshold={best['threshold']:.2f}")
    plt.tight_layout()
    best_bar_path = out_dir / f"{prefix}_best_metrics.png"
    plt.savefig(best_bar_path, dpi=150)
    plt.close()

    # Confusion matrix at best threshold
    y_pred_best = (y_score >= best["threshold"]).astype(int)
    cm = confusion_matrix(y_true, y_pred_best, labels=[0, 1])
    plt.figure(figsize=(5, 4))
    im = plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title("Confusion Matrix (Best Threshold)")
    plt.colorbar(im, fraction=0.046, pad=0.04)
    tick_marks = [0, 1]
    plt.xticks(tick_marks, ["Pred 0", "Pred 1"]) 
    plt.yticks(tick_marks, ["True 0", "True 1"]) 
    thresh = cm.max() / 2.0 if cm.max() else 0.5
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'), ha="center", va="center",
                     color="white" if cm[i, j] > thresh else "black")
    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    plt.tight_layout()
    cm_path = out_dir / f"{prefix}_confusion_matrix.png"
    plt.savefig(cm_path, dpi=150)
    plt.close()

    return {
        "classification_threshold_value": thr_val,
        "thresholds": thresholds.tolist(),
        "accuracy": acc_list,
        "precision": prec_list,
        "f1": f1_list,
        "best": best,
        "artifacts": {
            "metrics_vs_threshold": str(metrics_vs_thr_path),
            "best_metrics_bar": str(best_bar_path),
            "confusion_matrix": str(cm_path),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate order total model with regression and classification diagnostics.")
    parser.add_argument("--limit", type=int, default=5000, help="Max orders to evaluate (after grouping)")
    parser.add_argument("--delivered-only", action="store_true", help="Use only delivered orders")
    parser.add_argument("--model-path", type=str, default=str(Path(__file__).resolve().parent / "models" / "order_total_model.pkl"))
    parser.add_argument("--reports-dir", type=str, default=str(Path(__file__).resolve().parent / "reports"))
    parser.add_argument("--classification-threshold", type=float, default=None, help="Absolute threshold for high-value classification; if not set, use 0.8 quantile")
    parser.add_argument("--classification-quantile", type=float, default=0.8, help="Quantile for high-value classification when threshold not provided")
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    engine = get_engine()
    df = load_order_features(engine, limit=args.limit, delivered_only=args.delivered_only)
    if df.empty:
        raise SystemExit("No data returned from database for evaluation.")

    feature_cols = ["num_items", "avg_item_price", "total_items_price", "freight_value"]
    X = df[feature_cols].astype(float).values
    y = df["order_total"].astype(float).values

    model_path = Path(args.model_path)
    model = load_or_train_model(X, y, model_path)

    # If we trained a fallback model and model_path didn't exist, save it for reuse
    if not model_path.exists():
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path)

    # Hold-out evaluation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    if hasattr(model, "fit"):
        model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    reg_metrics = regression_diagnostics(y_test, y_pred, reports_dir)
    cls_metrics = classification_curves(
        y_true_reg=y_test,
        y_score_reg=y_pred,
        out_dir=reports_dir,
        threshold=args.classification_threshold,
        quantile=args.classification_quantile,
    )

    metrics_sweep = plot_metrics_vs_threshold(
        y_true_reg=y_test,
        y_score_reg=y_pred,
        out_dir=reports_dir,
        quantile=args.classification_quantile,
    )

    summary = {
        "samples_total": int(df.shape[0]),
        "features": feature_cols,
        "regression": reg_metrics,
        "classification": cls_metrics,
        "classification_metrics_sweep": metrics_sweep,
        "artifacts": {
            "parity_plot": str(reports_dir / "order_total_parity.png"),
            "residuals_plot": str(reports_dir / "order_total_residuals.png"),
            "roc_curve": str(reports_dir / "order_total_roc.png"),
            "pr_curve": str(reports_dir / "order_total_pr.png"),
            "metrics_vs_threshold": str(reports_dir / "order_total_metrics_vs_threshold.png"),
            "best_metrics_bar": str(reports_dir / "order_total_best_metrics.png"),
            "confusion_matrix": str(reports_dir / "order_total_confusion_matrix.png"),
            "model_path": str(model_path),
        },
    }

    with open(reports_dir / "evaluation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
