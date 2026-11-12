"""train_random_forest.py
================================
Random Forest baseline for fatigue prediction.

* Uses the same engineered dataset and exact 16 feature columns as the
  Logistic Regression baseline.
* Re‑creates the identical participant‑wise StratifiedGroupKFold split (the
  first fold is held out as the test set) so that the training and test
  observations match those used for the LR model.
* Trains two RandomForest models:
    – **Unweighted** – class_weight=None
    – **Balanced** – class_weight='balanced'
* Evaluates each model on the held‑out test participants and saves:
    – the fitted pipeline (`.joblib`)
    – evaluation metrics (JSON)
    – confusion matrix (CSV)
    – classification report (text)
    – feature‑importance table (CSV) and a horizontal bar‑chart (PNG)

All artefacts are written under a dedicated ``random_forest`` folder for
evaluation outputs and under ``models`` for the serialized pipelines.  The
script creates the required directories automatically and does **not** modify
the original dataset.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline

# ---------------------------------------------------------------------------
# Configuration – feature names, target, paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "engineered_dataset.csv"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
# Folder for all Random Forest artefacts (metrics, plots, reports)
RF_OUTPUT_DIR = ROOT / "random_forest"
RF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURES: List[str] = [
    "sleep_duration_min",
    "sleep_efficiency_pct",
    "sleep_fragmentation_index",
    "sleep_onset_latency_min",
    "total_steps",
    "active_minutes",
    "mvpa_minutes",
    "sedentary_minutes",
    "peak_activity_intensity",
    "resting_hr_bpm",
    "hr_mean_bpm",
    "hr_range_bpm",
    "hr_elevation_ratio",
    "hr_high_intensity_frac",
    "hr_temporal_consistency",
    "fitbit_wear_fraction",
]
TARGET = "tired_yesterday_code"
GROUP_COL = "user_id"

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    missing = set(FEATURES + [TARGET, GROUP_COL]) - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing columns in engineered dataset: {missing}")
    return df


def split_data(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    X = df[FEATURES]
    y = df[TARGET]
    groups = df[GROUP_COL]
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    train_idx, test_idx = next(sgkf.split(X, y, groups))
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Validation – same as LR script
    if set(train_df[GROUP_COL]).intersection(set(test_df[GROUP_COL])):
        raise RuntimeError("Participant overlap between train and test sets.")
    missing_train = set(range(5)) - set(train_df[TARGET].unique())
    if missing_train:
        raise RuntimeError(f"Training split missing classes: {missing_train}")
    missing_test = set(range(5)) - set(test_df[TARGET].unique())
    if missing_test:
        print(f"[INFO] Test split does NOT contain classes: {sorted(missing_test)}")
    else:
        print("[INFO] Test split contains all five fatigue classes.")

    print("--- Split Summary ---")
    print(f"Train rows: {train_df.shape[0]}, unique participants: {train_df[GROUP_COL].nunique()}")
    print(f"Test  rows: {test_df.shape[0]}, unique participants: {test_df[GROUP_COL].nunique()}")
    print("Train class distribution:")
    print(train_df[TARGET].value_counts().sort_index())
    print("Test class distribution:")
    print(test_df[TARGET].value_counts().sort_index())

    return {"train": train_df, "test": test_df}


def build_pipeline(class_weight: str | None = None) -> Pipeline:
    """Create a Pipeline that median‑imputes and fits a RandomForest.

    Parameters
    ----------
    class_weight : str | None
        Pass ``'balanced'`` for the experimental model, otherwise ``None``.
    """
    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])
    preprocessor = ColumnTransformer([
        ("num", numeric_transformer, FEATURES)
    ], remainder="drop")
    clf = RandomForestClassifier(
        n_estimators=500,
        random_state=42,
        max_features="sqrt",
        class_weight=class_weight,
        n_jobs=-1,
    )
    pipe = Pipeline([("preprocess", preprocessor), ("clf", clf)])
    return pipe


def evaluate_model(model_pipe: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, any]:
    y_pred = model_pipe.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
        "macro_precision": precision_score(y_test, y_pred, average="macro", zero_division=0),
        "macro_recall": recall_score(y_test, y_pred, average="macro", zero_division=0),
        "macro_f1": f1_score(y_test, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_test, y_pred, average="weighted", zero_division=0),
        "classification_report": classification_report(
            y_test,
            y_pred,
            target_names=[
                "not_at_all",
                "a_little_bit",
                "somewhat",
                "quite_a_bit",
                "very_much",
            ],
            output_dict=True,
        ),
        "confusion_matrix": confusion_matrix(y_test, y_pred),
    }
    return metrics


def save_metrics(model_pipe: Pipeline, metrics: Dict[str, any], prefix: str, test_df: pd.DataFrame) -> None:
    """Write metrics JSON, confusion matrix CSV and classification report.
    All artefacts are stored under ``RF_OUTPUT_DIR`` with ``prefix`` as filename
    stem (e.g., ``random_forest`` or ``random_forest_balanced``).
    """
    # JSON (including split info)
    json_path = RF_OUTPUT_DIR / f"{prefix}_metrics.json"
    serialisable = {
        k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in metrics.items()
    }
    serialisable["test_rows"] = test_df.shape[0]
    serialisable["test_participants"] = int(test_df[GROUP_COL].nunique())
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(serialisable, f, indent=2)
    print(f"Saved metrics JSON to {json_path}")

    # Confusion matrix CSV
    cm_path = RF_OUTPUT_DIR / f"{prefix}_confusion_matrix.csv"
    cm_df = pd.DataFrame(
        metrics["confusion_matrix"],
        index=["not_at_all", "a_little_bit", "somewhat", "quite_a_bit", "very_much"],
        columns=[
            "pred_not_at_all",
            "pred_a_little_bit",
            "pred_somewhat",
            "pred_quite_a_bit",
            "pred_very_much",
        ],
    )
    cm_df.to_csv(cm_path, index=True)
    print(f"Saved confusion matrix CSV to {cm_path}")

    # Human‑readable classification report
    report_path = RF_OUTPUT_DIR / f"{prefix}_classification_report.txt"
    report_str = classification_report(
        test_df[TARGET],
        model_pipe.predict(test_df[FEATURES]),
        target_names=[
            "not_at_all",
            "a_little_bit",
            "somewhat",
            "quite_a_bit",
            "very_much",
        ],
    )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_str)
    print(f"Saved classification report to {report_path}")


def save_feature_importance(model_pipe: Pipeline, prefix: str) -> None:
    """Extract feature importances from the RandomForest and save a CSV and bar chart
    under ``RF_OUTPUT_DIR``.
    """
    importances = model_pipe.named_steps["clf"].feature_importances_
    imp_df = pd.DataFrame({
        "feature": FEATURES,
        "importance": importances,
    }).sort_values(by="importance", ascending=False)
    csv_path = RF_OUTPUT_DIR / f"{prefix}_feature_importance.csv"
    imp_df.to_csv(csv_path, index=False)
    print(f"Saved feature‑importance CSV to {csv_path}")

    # Horizontal bar chart
    plt.figure(figsize=(8, 6))
    sns.barplot(x="importance", y="feature", data=imp_df, palette="viridis")
    plt.title(f"Feature Importance – {prefix.replace('_', ' ').title()}")
    plt.xlabel("Mean Decrease in Impurity")
    plt.ylabel("")
    plt.tight_layout()
    img_path = RF_OUTPUT_DIR / f"{prefix}_feature_importance.png"
    plt.savefig(img_path, dpi=150)
    plt.close()
    print(f"Saved feature‑importance plot to {img_path}")


def main() -> None:
    df = load_data()
    splits = split_data(df)
    train_df = splits["train"]
    test_df = splits["test"]

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]
    X_test = test_df[FEATURES]
    y_test = test_df[TARGET]

    # ---------------------------------------------------------------------
    # 1️⃣ Unweighted Random Forest
    # ---------------------------------------------------------------------
    unweighted_pipe = build_pipeline(class_weight=None)
    unweighted_pipe.fit(X_train, y_train)
    metrics_unweighted = evaluate_model(unweighted_pipe, X_test, y_test)
    print("\n--- Unweighted Random Forest Evaluation ---")
    print(f"Accuracy: {metrics_unweighted['accuracy']:.4f}")
    print(f"Balanced accuracy: {metrics_unweighted['balanced_accuracy']:.4f}")
    print(f"Macro F1: {metrics_unweighted['macro_f1']:.4f}\n")
    # Save artefacts
    joblib.dump(unweighted_pipe, MODEL_DIR / "random_forest_model.joblib")
    print(f"Saved unweighted model to {MODEL_DIR / 'random_forest_model.joblib'}")
    save_metrics(unweighted_pipe, metrics_unweighted, "random_forest", test_df)
    save_feature_importance(unweighted_pipe, "random_forest")

    # ---------------------------------------------------------------------
    # 2️⃣ Balanced Random Forest (class_weight='balanced')
    # ---------------------------------------------------------------------
    balanced_pipe = build_pipeline(class_weight="balanced")
    balanced_pipe.fit(X_train, y_train)
    metrics_balanced = evaluate_model(balanced_pipe, X_test, y_test)
    print("\n--- Balanced Random Forest Evaluation ---")
    print(f"Accuracy: {metrics_balanced['accuracy']:.4f}")
    print(f"Balanced accuracy: {metrics_balanced['balanced_accuracy']:.4f}")
    print(f"Macro F1: {metrics_balanced['macro_f1']:.4f}\n")
    # Save artefacts
    joblib.dump(balanced_pipe, MODEL_DIR / "random_forest_balanced_model.joblib")
    print(f"Saved balanced model to {MODEL_DIR / 'random_forest_balanced_model.joblib'}")
    save_metrics(balanced_pipe, metrics_balanced, "random_forest_balanced", test_df)
    save_feature_importance(balanced_pipe, "random_forest_balanced")

    # Summary printed to stdout
    print("\n=== Summary of Test Set ===")
    print(f"Observations: {X_test.shape[0]}, Participants: {test_df[GROUP_COL].nunique()}")
    print("Both models evaluated on the same split.")


if __name__ == "__main__":
    main()
