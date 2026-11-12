"""EDA for the engineered OULAD score dataset (same layout as fatigue_model/src/eda.py).

Reads ``score_model/data/processed/engineered_dataset.csv.gz`` (read-only) and writes
plots plus ``eda_report.txt`` to ``score_model/docs/eda``. The target is a 0-100 score,
so box plots group rows into score bands instead of fatigue classes.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

import pipeline as pit  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "engineered_dataset.csv.gz"
OUTPUT_DIR = ROOT / "docs" / "eda"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "score"
BAND_EDGES = [0, 40, 60, 80, 100.01]  # OULAD pass mark is 40
BAND_LABELS = ["<40 (fail)", "40-59", "60-79", "80-100"]

df = pd.read_csv(DATA_PATH)
pit.enable_vle_features()
numeric_cols = [c for c in pit.NUMERIC_FEATURES if c in df.columns]
df["score_band"] = pd.cut(df[TARGET], BAND_EDGES, labels=BAND_LABELS, right=False)
assert df["score_band"].notna().all()

report = []


def save_fig(fig, name):
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / f"{name}.png", dpi=150)
    plt.close(fig)


# 1. Overview
report += ["# Exploratory Data Analysis Report - OULAD score dataset", "",
           f"**Rows:** {len(df)}", f"**Columns:** {df.shape[1] - 1}",
           f"**Students:** {df['id_student'].nunique()}", "",
           "## Rows per split", "", df["split"].value_counts().reindex(["train", "val", "test"]).to_string(), "",
           "## Data types & missing values", "",
           pd.DataFrame({"dtype": df.dtypes, "missing": df.isna().sum(),
                         "missing_pct": (100 * df.isna().mean()).round(2)}).to_string(), ""]

# 2. Descriptive statistics
report += ["## Descriptive statistics (numeric features)", "",
           df[numeric_cols].describe().transpose().to_string(), ""]

# 3. Feature distributions
for col in numeric_cols:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(df[col].dropna(), kde=True, ax=ax, bins=30, color="steelblue")
    ax.set_title(f"Distribution of {col}")
    ax.set_xlabel(col)
    ax.set_ylabel("Count")
    save_fig(fig, f"dist_{col}")

# 4. Correlation heatmap (features + target) and correlation with the target
corr = df[numeric_cols + [TARGET]].corr()
fig, ax = plt.subplots(figsize=(14, 12))
sns.heatmap(corr, cmap="coolwarm", center=0, square=True, linewidths=.5, ax=ax)
ax.set_title("Feature Correlation Heatmap (Pearson)")
save_fig(fig, "correlation_heatmap")

target_corr = corr[TARGET].drop(TARGET).sort_values()
fig, ax = plt.subplots(figsize=(7, 9))
target_corr.plot.barh(ax=ax, color=np.where(target_corr > 0, "tab:blue", "tab:red"))
ax.axvline(0, color="black", lw=0.8)
ax.set_title("Correlation of each feature with score")
ax.set_xlabel("Pearson r")
save_fig(fig, "correlation_with_score")
report += ["## Correlation with score (Pearson, sorted)", "",
           target_corr.sort_values(key=np.abs, ascending=False).round(3).to_string(), ""]

# 5. Target distribution
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
sns.histplot(df[TARGET], bins=50, ax=axes[0], color="steelblue")
axes[0].set_title("Score distribution")
axes[0].set_xlabel("score (0-100)")
counts = df["score_band"].value_counts().reindex(BAND_LABELS)
sns.barplot(x=BAND_LABELS, y=counts.values, hue=BAND_LABELS, legend=False, ax=axes[1], palette="viridis")
axes[1].set_title("Score bands")
axes[1].set_xlabel("score band")
axes[1].set_ylabel("Count")
save_fig(fig, "score_distribution")
report += ["## Score distribution", "", df[TARGET].describe().to_string(), "",
           "Score bands:", counts.to_string(), ""]

# 6. Score by assessment type and module
for col in ["assessment_type", "code_module", "code_presentation"]:
    order = sorted(df[col].unique())
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.boxplot(x=col, y=TARGET, data=df, order=order, hue=col, legend=False, ax=ax, palette="Set2")
    ax.set_title(f"Score by {col}")
    save_fig(fig, f"score_by_{col}")
    report += [f"## Score by {col}", "", df.groupby(col)[TARGET].agg(["count", "mean", "median", "std"]).round(2).to_string(), ""]

# 7. Feature vs. score band
for col in numeric_cols:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.boxplot(x="score_band", y=col, data=df, order=BAND_LABELS, hue="score_band", legend=False,
                ax=ax, palette="Set2", showfliers=False)
    ax.set_xlabel("Score band")
    ax.set_ylabel(col)
    ax.set_title(f"{col} by score band")
    save_fig(fig, f"box_{col}")

# 8. Outliers (> 3 std from the mean; NaN never counts)
z = (df[numeric_cols] - df[numeric_cols].mean()).abs() > 3 * df[numeric_cols].std()
report += ["## Outlier summary", "",
           f"Rows flagged as outliers (|value-mean| > 3 x std in any feature): {int(z.any(axis=1).sum())} of {len(df)}", "",
           "Per feature:", z.sum().sort_values(ascending=False).to_string(), ""]

(OUTPUT_DIR / "eda_report.txt").write_text("\n".join(report), encoding="utf-8")
print("EDA figures and report saved to:", OUTPUT_DIR)
