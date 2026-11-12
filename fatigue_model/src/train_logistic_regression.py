"""train_logistic_regression.py
================================
Baseline multiclass Logistic Regression model for fatigue prediction.

* Reads the engineered dataset (engineered_dataset.csv).
* Uses the 16 engineered feature columns listed in the task description.
* Performs a participant‑wise stratified 5‑fold split using
  ``StratifiedGroupKFold`` (one fold is held‑out for testing).
* Builds a scikit‑learn ``Pipeline`` with median imputation and
  ``StandardScaler`` followed by ``LogisticRegression``.
* Trains on the training split, evaluates on the test split, and saves
  the fitted pipeline, evaluation metrics, classification report and
  confusion matrix.

The script is deliberately **self‑contained** – it creates any required
output directories at runtime and prints a concise summary.  It does *not*
modify the original dataset.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
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
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Configuration – feature names, target, paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "engineered_dataset.csv"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
DOCS_EDA_DIR = ROOT / "docs" / "eda"  # for evaluation artefacts
DOCS_EDA_DIR.mkdir(parents=True, exist_ok=True)

# Features required by the baseline (exact order is not important)
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
    """Load the engineered dataset.

    Returns
    -------
    pd.DataFrame
        The full dataset with all columns.
    """
    df = pd.read_csv(DATA_PATH)
    # sanity check – ensure required columns exist
    missing = set(FEATURES + [TARGET, GROUP_COL]) - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing columns in engineered dataset: {missing}")
    return df


def split_data(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Perform a single StratifiedGroupKFold split.

    One of the five folds is used as the test set; the others form the
    training set. The function returns a dict with keys ``train`` and ``test``
    containing the respective DataFrames.
    """
    X = df[FEATURES]
    y = df[TARGET]
    groups = df[GROUP_COL]

    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    # Take the first split as test – any fold would be acceptable.
    train_idx, test_idx = next(sgkf.split(X, y, groups))

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # ----- Validation of split requirements -----
    # 1. No participant appears in both sets
    train_groups = set(train_df[GROUP_COL])
    test_groups = set(test_df[GROUP_COL])
    overlap = train_groups.intersection(test_groups)
    if overlap:
        raise RuntimeError(
            f"Participant overlap between train and test sets: {overlap}"
        )

    # 2. All five classes present in training set
    missing_train_classes = set(range(5)) - set(train_df[TARGET].unique())
    if missing_train_classes:
        raise RuntimeError(
            f"Training split missing fatigue classes: {missing_train_classes}"
        )

    # 3. Report presence of all classes in test set (not a hard error)
    missing_test_classes = set(range(5)) - set(test_df[TARGET].unique())
    if missing_test_classes:
        print(
            f"[INFO] Test split does NOT contain classes: {sorted(missing_test_classes)}"
        )
    else:
        print("[INFO] Test split contains all five fatigue classes.")

    # 4. Summary statistics
    print("--- Split Summary ---")
    print(f"Train rows: {train_df.shape[0]}, unique participants: {train_df[GROUP_COL].nunique()}")
    print(f"Test  rows: {test_df.shape[0]}, unique participants: {test_df[GROUP_COL].nunique()}")
    print("Train class distribution:")
    print(train_df[TARGET].value_counts().sort_index())
    print("Test class distribution:")
    print(test_df[TARGET].value_counts().sort_index())

    return {"train": train_df, "test": test_df}


def build_pipeline() -> Pipeline:
    """Create a scikit‑learn Pipeline with median imputation, scaling and
    Logistic Regression.
    """
    numeric_transformer = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    preprocessor = ColumnTransformer(
        [("num", numeric_transformer, FEATURES)], remainder="drop"
    )
    # ``multi_class`` parameter is omitted for compatibility with older
    # scikit‑learn versions where it may not be supported. ``solver='lbfgs'``
    # automatically enables multinomial handling when the target has >2 classes.
    clf = LogisticRegression(
        max_iter=2000,
        random_state=42,
        solver="lbfgs",
    )
    pipe = Pipeline([("preprocess", preprocessor), ("clf", clf)])
    return pipe


def evaluate_model(pipe: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, any]:
    """Calculate evaluation metrics and return a dictionary.
    """
    y_pred = pipe.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
        "macro_precision": precision_score(y_test, y_pred, average="macro", zero_division=0),
        "macro_recall": recall_score(y_test, y_pred, average="macro", zero_division=0),
        "macro_f1": f1_score(y_test, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_test, y_pred, average="weighted", zero_division=0),
        "classification_report": classification_report(
            y_test, y_pred, target_names=[
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


def save_artifacts(
    pipe: Pipeline, metrics: Dict[str, any], test_df: pd.DataFrame
) -> None:
    """Persist the model pipeline and evaluation artefacts.

    Parameters
    ----------
    pipe : Pipeline
        Fitted preprocessing + classifier pipeline.
    metrics : dict
        Dictionary returned by ``evaluate_model``.
    test_df : pd.DataFrame
        Test split – used to report the number of observations and participants.
    """
    # 1. Model pipeline
    model_path = MODEL_DIR / "logistic_regression_model.joblib"
    joblib.dump(pipe, model_path)
    print(f"Saved model pipeline to {model_path}")

    # 2. Metrics JSON (easy to re‑load programmatically)
    metrics_path = DOCS_EDA_DIR / "logistic_regression_metrics.json"
    # Convert numpy arrays to regular lists for JSON serialisation
    serialisable = {
        k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in metrics.items()
    }
    # Add split information for reference
    serialisable["test_rows"] = test_df.shape[0]
    serialisable["test_participants"] = int(test_df[GROUP_COL].nunique())
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(serialisable, f, indent=2)
    print(f"Saved evaluation metrics to {metrics_path}")

    # 3. Confusion matrix CSV (human‑readable)
    cm_path = DOCS_EDA_DIR / "confusion_matrix.csv"
    cm_df = pd.DataFrame(
        metrics["confusion_matrix"],
        index=["not_at_all", "a_little_bit", "somewhat", "quite_a_bit", "very_much"],
        columns=["pred_not_at_all", "pred_a_little_bit", "pred_somewhat", "pred_quite_a_bit", "pred_very_much"],
    )
    cm_df.to_csv(cm_path, index=True)
    print(f"Saved confusion matrix CSV to {cm_path}")

    # 4. Human‑readable classification report text file
    report_path = DOCS_EDA_DIR / "classification_report.txt"
    report_str = classification_report(
        test_df[TARGET],
        pipe.predict(test_df[FEATURES]),
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


def main() -> None:
    df = load_data()
    splits = split_data(df)
    train_df = splits["train"]
    test_df = splits["test"]

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]
    X_test = test_df[FEATURES]
    y_test = test_df[TARGET]

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    print("Model training completed.")

    metrics = evaluate_model(pipeline, X_test, y_test)

    # Print a concise summary to stdout
    print("\n--- Evaluation Summary ---")
    print(f"Test observations : {X_test.shape[0]}")
    print(f"Test participants : {test_df[GROUP_COL].nunique()}")
    print(f"Accuracy          : {metrics['accuracy']:.4f}")
    print(f"Balanced accuracy : {metrics['balanced_accuracy']:.4f}")
    print(f"Macro F1          : {metrics['macro_f1']:.4f}")
    print(f"Weighted F1       : {metrics['weighted_f1']:.4f}")

    save_artifacts(pipeline, metrics, test_df)


if __name__ == "__main__":
    main()
