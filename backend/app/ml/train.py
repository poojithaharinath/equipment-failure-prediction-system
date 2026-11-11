import os
import json
import logging
import joblib
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.ml.feature_engineering import FeatureExtractor, FEATURE_COLUMNS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MLTraining")

def train_and_evaluate_models():
    db = SessionLocal()
    try:
        extractor = FeatureExtractor(db)
        # Use 1.0 day time step for rich dataset
        df = extractor.build_chronological_dataset(time_step_days=1.0, prediction_horizon_hours=24)

        # Save processed feature matrix
        os.makedirs("data/processed", exist_ok=True)
        csv_path = "data/processed/feature_matrix.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Processed feature matrix saved to {csv_path}")

        # Chronological Split: 75% train (earlier), 25% test (later)
        df_sorted = df.sort_values(by="as_of_time").reset_index(drop=True)
        split_idx = int(len(df_sorted) * 0.75)
        train_df = df_sorted.iloc[:split_idx]
        test_df = df_sorted.iloc[split_idx:]

        X_train = train_df[FEATURE_COLUMNS]
        y_train = train_df["failure_in_24h"]
        X_test = test_df[FEATURE_COLUMNS]
        y_test = test_df["failure_in_24h"]

        logger.info(f"Train samples: {len(X_train)} (Failures: {y_train.sum()}), Test samples: {len(X_test)} (Failures: {y_test.sum()})")

        # Scaler
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # -------------------------------------------------------------
        # 1. Random Forest Classifier
        # -------------------------------------------------------------
        rf = RandomForestClassifier(
            n_estimators=120,
            max_depth=8,
            class_weight="balanced",
            random_state=settings.RANDOM_SEED,
            n_jobs=-1
        )
        rf.fit(X_train, y_train)
        rf_preds = rf.predict(X_test)
        rf_probs = rf.predict_proba(X_test)[:, 1]

        rf_cm = confusion_matrix(y_test, rf_preds)
        rf_tn, rf_fp, rf_fn, rf_tp = rf_cm.ravel()

        rf_metrics = {
            "model_type": "RandomForestClassifier",
            "accuracy": round(float(accuracy_score(y_test, rf_preds)), 4),
            "precision": round(float(precision_score(y_test, rf_preds, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, rf_preds, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_test, rf_preds, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, rf_probs)), 4) if len(np.unique(y_test)) > 1 else 1.0,
            "confusion_matrix": {
                "true_negatives": int(rf_tn),
                "false_positives": int(rf_fp),
                "false_negatives": int(rf_fn),
                "true_positives": int(rf_tp)
            },
            "failures_detected_in_advance": int(rf_tp),
            "missed_failures": int(rf_fn),
            "false_alarms": int(rf_fp),
            "feature_importances": {
                feat: round(float(imp), 4)
                for feat, imp in zip(FEATURE_COLUMNS, rf.feature_importances_)
            }
        }

        # -------------------------------------------------------------
        # 2. Logistic Regression Comparison
        # -------------------------------------------------------------
        lr = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=settings.RANDOM_SEED
        )
        lr.fit(X_train_scaled, y_train)
        lr_preds = lr.predict(X_test_scaled)
        lr_probs = lr.predict_proba(X_test_scaled)[:, 1]

        lr_cm = confusion_matrix(y_test, lr_preds)
        lr_tn, lr_fp, lr_fn, lr_tp = lr_cm.ravel()

        lr_metrics = {
            "model_type": "LogisticRegression",
            "accuracy": round(float(accuracy_score(y_test, lr_preds)), 4),
            "precision": round(float(precision_score(y_test, lr_preds, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, lr_preds, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_test, lr_preds, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, lr_probs)), 4) if len(np.unique(y_test)) > 1 else 1.0,
            "confusion_matrix": {
                "true_negatives": int(lr_tn),
                "false_positives": int(lr_fp),
                "false_negatives": int(lr_fn),
                "true_positives": int(lr_tp)
            },
            "failures_detected_in_advance": int(lr_tp),
            "missed_failures": int(lr_fn),
            "false_alarms": int(lr_fp)
        }

        # Save the primary Random Forest model bundle
        model_bundle = {
            "model": rf,
            "scaler": scaler,
            "feature_columns": FEATURE_COLUMNS,
            "trained_at": datetime.utcnow().isoformat(),
            "metrics": rf_metrics,
            "random_seed": settings.RANDOM_SEED,
            "prediction_horizon_hours": 24,
            "threshold_low": settings.RISK_THRESHOLD_LOW,
            "threshold_high": settings.RISK_THRESHOLD_HIGH
        }

        os.makedirs(os.path.dirname(settings.MODEL_PATH), exist_ok=True)
        joblib.dump(model_bundle, settings.MODEL_PATH)
        logger.info(f"Model bundle saved to {settings.MODEL_PATH}")

        # Combined Evaluation Report
        evaluation_report = {
            "report_generated_at": datetime.utcnow().isoformat(),
            "target": "Equipment Failure within Next 24 Hours",
            "train_set_size": len(X_train),
            "test_set_size": len(X_test),
            "total_test_failures": int(y_test.sum()),
            "champion_model": rf_metrics,
            "baseline_model": lr_metrics,
            "comparison_summary": {
                "rf_f1_vs_lr": round(rf_metrics["f1_score"] - lr_metrics["f1_score"], 4),
                "rf_recall_vs_lr": round(rf_metrics["recall"] - lr_metrics["recall"], 4),
                "rf_accuracy_vs_lr": round(rf_metrics["accuracy"] - lr_metrics["accuracy"], 4),
                "winner": "RandomForestClassifier" if rf_metrics["f1_score"] >= lr_metrics["f1_score"] else "LogisticRegression"
            }
        }

        os.makedirs("data/reports", exist_ok=True)
        report_path = "data/reports/model_evaluation_report.json"
        with open(report_path, "w") as f:
            json.dump(evaluation_report, f, indent=2)
        logger.info(f"Model evaluation report saved to {report_path}")

        return evaluation_report

    finally:
        db.close()

if __name__ == "__main__":
    rep = train_and_evaluate_models()
    print("Model Training & Evaluation Report:")
    print(json.dumps(rep, indent=2))
