# EDA script for the engineered fatigue dataset
# -------------------------------------------------
# This script loads ``fatigue_model/data/processed/engineered_dataset.csv`` and
# performs a set of exploratory data analysis steps.  It **does not** modify the
# dataset – it only reads it, generates visualisations and writes a concise
# textual report.
#
# All output files are placed under ``docs/eda`` which is created automatically
# if it does not exist.
# -------------------------------------------------

import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "engineered_dataset.csv"
OUTPUT_DIR = ROOT / "docs" / "eda"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Load dataset
# ---------------------------------------------------------------------------
df = pd.read_csv(DATA_PATH)

# Keep only metadata columns for reference (they are not used as predictors)
metadata_cols = ["user_id", "activity_date"]
target_col = "tired_yesterday_code"
feature_cols = [c for c in df.columns if c not in metadata_cols + [target_col]]

# ---------------------------------------------------------------------------
# Helper: save figure with a consistent style
# ---------------------------------------------------------------------------
def save_fig(fig, name, tight=True):
    fp = OUTPUT_DIR / f"{name}.png"
    if tight:
        fig.tight_layout()
    fig.savefig(fp, dpi=150)
    plt.close(fig)

# ---------------------------------------------------------------------------
# 1. Basic dataset overview
# ---------------------------------------------------------------------------
with open(OUTPUT_DIR / "eda_report.txt", "w", encoding="utf-8") as rep:
    rep.write("# Exploratory Data Analysis Report\n\n")
    rep.write(f"**Rows:** {df.shape[0]}\n")
    rep.write(f"**Columns:** {df.shape[1]}\n\n")
    rep.write("## Data types & missing values\n\n")
    dtype_missing = pd.DataFrame({
        "dtype": df.dtypes,
        "missing": df.isna().sum()
    })
    rep.write(dtype_missing.to_string())
    rep.write("\n\n")

# ---------------------------------------------------------------------------
# 2. Descriptive statistics for engineered features
# ---------------------------------------------------------------------------
stats = df[feature_cols].describe().transpose()
with open(OUTPUT_DIR / "eda_report.txt", "a", encoding="utf-8") as rep:
    rep.write("## Descriptive statistics (engineered features)\n\n")
    rep.write(stats.to_string())
    rep.write("\n\n")

# ---------------------------------------------------------------------------
# 3. Feature distribution plots (histograms + KDE)
# ---------------------------------------------------------------------------
for col in feature_cols:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(df[col].dropna(), kde=True, ax=ax, bins=30, color="steelblue")
    ax.set_title(f"Distribution of {col}")
    ax.set_xlabel(col)
    ax.set_ylabel("Count")
    save_fig(fig, f"dist_{col}")

# ---------------------------------------------------------------------------
# 4. Correlation matrix (Pearson) for engineered features
# ---------------------------------------------------------------------------
corr = df[feature_cols].corr()
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr, cmap="coolwarm", center=0, square=True, linewidths=.5, ax=ax)
ax.set_title("Feature Correlation Heatmap (Pearson)")
save_fig(fig, "correlation_heatmap")

# ---------------------------------------------------------------------------
# 5. Fatigue target distribution
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 4))
order = [0, 1, 2, 3, 4]
labels = ["not_at_all", "a_little_bit", "somewhat", "quite_a_bit", "very_much"]
counts = df[target_col].value_counts().reindex(order).fillna(0).astype(int)
sns.barplot(x=labels, y=counts.values, ax=ax, palette="viridis")
ax.set_xlabel("Fatigue (tired_yesterday_code)")
ax.set_ylabel("Count")
ax.set_title("Fatigue target class distribution")
save_fig(fig, "fatigue_distribution")

# Record in report
with open(OUTPUT_DIR / "eda_report.txt", "a", encoding="utf-8") as rep:
    rep.write("## Fatigue target distribution\n\n")
    rep.write(counts.to_string())
    rep.write("\n\n")

# ---------------------------------------------------------------------------
# 6. Feature vs. fatigue relationships (boxplots)
# ---------------------------------------------------------------------------
for col in feature_cols:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.boxplot(x=target_col, y=col, data=df, order=order, ax=ax, palette="Set2")
    ax.set_xlabel("Fatigue class")
    ax.set_ylabel(col)
    ax.set_title(f"{col} by fatigue class")
    save_fig(fig, f"box_{col}")

# ---------------------------------------------------------------------------
# 7. Outlier analysis – identify rows where any feature lies > 3 std devs
# ---------------------------------------------------------------------------
outlier_mask = (np.abs(df[feature_cols] - df[feature_cols].mean()) > 3 * df[feature_cols].std()).any(axis=1)
outlier_count = outlier_mask.sum()
with open(OUTPUT_DIR / "eda_report.txt", "a", encoding="utf-8") as rep:
    rep.write("## Outlier summary\n\n")
    rep.write(f"Rows flagged as outliers (|value‑mean| > 3 × std): {outlier_count} of {df.shape[0]}\n")
    rep.write("\n")

# ---------------------------------------------------------------------------
# End of script – all artefacts are now written to ``docs/eda``.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("EDA script executed – figures and report saved to:", OUTPUT_DIR)

