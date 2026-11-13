"""Point-in-time feature generation and leakage tests for the OULAD benchmark.

Design
------
Each row is one student-assessment attempt.  A row's features are generated as
of::

    prediction_time = deadline - PREDICTION_HORIZON_DAYS

i.e. a fixed point before the assessment is due, which mirrors CogniSync
predicting a quiz *before* it is taken.  The prediction instant never depends
on when (or whether) the student submits the target, so the target's own
submission timing cannot leak into the features.  Visible history is every
other attempt whose ``date_submitted`` is strictly earlier than that instant;
the target attempt itself is always excluded, even if it was submitted early.

Known simplification: a prior score is treated as known on its submission
day.  Real OULAD marking takes days, so the most recent visible score may not
have been released yet; this slightly favours the history features.

``studentInfo.final_result`` is never used.  ``studentVle.csv`` daily clicks
are an optional feature group (``load_oulad(with_vle=True)`` plus
``enable_vle_features()``) so score-only and score + engagement models can be
compared.  No mood/stress/fatigue signals exist in or are derived from OULAD.

Public API
----------
load_oulad()                    read the five assessment tables (+ studentVle)
enable_vle_features()           add the VLE engagement feature group
build_features()               one row per attempt, point-in-time features
chronological_student_split()  chronological cohorts, disjoint students
audit_point_in_time()          ordering / blocklist assertions
spot_check_features()          independent recomputation of prior stats
future_invariance_check()      strip future raw rows, features must not change
run_leakage_suite()            all of the above + deliberately leaky probes
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "oulad"

TRAIN_PRESENTATIONS = ("2013B", "2013J")
VAL_PRESENTATIONS = ("2014B",)
TEST_PRESENTATIONS = ("2014J",)

# Predict this many days before the deadline (a design parameter, not a fact).
PREDICTION_HORIZON_DAYS = 7.0

NUMERIC_FEATURES = [
    # history of the same module-presentation, strictly before prediction_time
    "prior_n",
    "prior_mean",
    "prior_std",
    "prior_min",
    "prior_max",
    "prior_last",
    "prior_weighted_mean",
    "prior_slope",
    "prior_delta_last2",
    "prior_mean_same_type",
    "prior_n_same_type",
    "prior_late_rate",
    "prior_mean_lateness",
    "days_since_last_sub",
    "prior_mean_gap",
    # cross-module history of the same student, still point-in-time
    "prior_n_all",
    "prior_mean_all",
    "prior_other_n",
    # assessment / enrolment metadata known before the target
    "assessment_weight",
    "assessment_day",
    "assessment_index_frac",
    "module_n_assessments",
    "days_since_registration",
    "module_presentation_length",
    "unregistered_before_pred",
    "num_of_prev_attempts",
    "studied_credits",
]

CATEGORICAL_FEATURES = [
    "assessment_type",
    "code_module",
    "code_presentation",
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "disability",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Optional engagement group from studentVle.csv, all strictly before prediction_time.
VLE_FEATURES = [
    "vle_clicks_total",
    "vle_clicks_7d",
    "vle_clicks_14d",
    "vle_active_days_14d",
    "vle_days_since_last_click",
]
ENROLMENT_KEY = ["id_student", "code_module", "code_presentation"]


def enable_vle_features() -> None:
    """Add VLE_FEATURES to the model inputs (in place, so imported references see it)."""
    if VLE_FEATURES[0] not in NUMERIC_FEATURES:
        NUMERIC_FEATURES.extend(VLE_FEATURES)
        FEATURE_COLUMNS[:] = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Anything matching these names must never reach the design matrix.
FORBIDDEN_FEATURE_PATTERNS = (
    "final_result",
    "target",
    "future",
    "leak",
    "score",  # includes the target ``score`` and any score of later attempts
)


# --------------------------------------------------------------------------- #
# Loading / cleaning
# --------------------------------------------------------------------------- #


def load_oulad(data_dir: str | Path | None = None, with_vle: bool = False) -> dict[str, pd.DataFrame]:
    """Load the five assessment/enrolment tables, plus daily studentVle clicks if asked.

    ``vle.csv`` (resource metadata) is never read.
    """
    root = Path(data_dir) if data_dir is not None else DATA_DIR
    tables = {
        "assessments": pd.read_csv(root / "assessments.csv", na_values=["?"]),
        "courses": pd.read_csv(root / "courses.csv", na_values=["?"]),
        "studentAssessment": pd.read_csv(root / "studentAssessment.csv", na_values=["?"]),
        "studentInfo": pd.read_csv(root / "studentInfo.csv", na_values=["?"]),
        "studentRegistration": pd.read_csv(root / "studentRegistration.csv", na_values=["?"]),
    }
    # Normalise the module length column name (OULAD.names calls it "length").
    courses = tables["courses"].rename(columns={"length": "module_presentation_length"})
    tables["courses"] = courses[["code_module", "code_presentation", "module_presentation_length"]]
    if with_vle:
        vle = pd.read_csv(
            root / "studentVle.csv",
            usecols=ENROLMENT_KEY + ["date", "sum_click"],
            dtype={"id_student": "int64", "date": "int32", "sum_click": "int32"},
        )
        # One row per enrolment-day; per-resource detail is not needed.
        tables["studentVle"] = vle.groupby(ENROLMENT_KEY + ["date"], as_index=False, sort=False)[
            "sum_click"
        ].sum()
    return tables


def clean_attempts(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Scored, non-banked attempts joined to assessment / enrolment metadata.

    Rows are kept even when the student has no prior attempt; the benchmark
    filters those out later.  Banked scores are transfers from an earlier
    presentation and are not evidence of work in this presentation.
    """
    sa = tables["studentAssessment"]
    keep = (sa["is_banked"] == 0) & sa["score"].notna()
    attempts = sa.loc[keep].copy()

    meta = assessment_metadata(tables)
    attempts = attempts.merge(
        meta,
        on="id_assessment",
        how="left",
        validate="many_to_one",
    )
    assert attempts["assessment_type"].notna().all()
    assert attempts["deadline"].notna().all()

    attempts = attempts.merge(
        tables["studentInfo"],
        on=["code_module", "code_presentation", "id_student"],
        how="left",
        validate="many_to_one",
    )
    # ``final_result`` is the end-of-module outcome: never a feature, not even
    # in the working frame.
    attempts = attempts.drop(columns=["final_result"])
    attempts = attempts.merge(
        tables["studentRegistration"][
            ["code_module", "code_presentation", "id_student", "date_registration", "date_unregistration"]
        ],
        on=["code_module", "code_presentation", "id_student"],
        how="left",
        validate="many_to_one",
    )
    attempts = attempts.merge(
        tables["courses"],
        on=["code_module", "code_presentation"],
        how="left",
        validate="many_to_one",
    )
    attempts["score"] = attempts["score"].astype(float)
    attempts["date_submitted"] = attempts["date_submitted"].astype(float)
    return attempts.reset_index(drop=True)


def assessment_metadata(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Assessment deadline proxy, curriculum position, and module size.

    Exams have no deadline in OULAD (``date`` is missing for 11 assessments).
    Their deadline is imputed as the end of the presentation, which is when
    exams are sat (median exam submission day 241 vs median module length 261;
    only 0.2% of exam submissions fall after the module end).
    """
    a = tables["assessments"].merge(
        tables["courses"], on=["code_module", "code_presentation"], how="left", validate="many_to_one"
    )
    a["deadline"] = a["date"].fillna(a["module_presentation_length"]).astype(float)
    a = a.sort_values(
        ["code_module", "code_presentation", "deadline", "id_assessment"], kind="mergesort"
    )
    group = a.groupby(["code_module", "code_presentation"], sort=False)
    a["assessment_index"] = group.cumcount().astype(float)
    a["module_n_assessments"] = group["id_assessment"].transform("size").astype(float)
    denom = (a["module_n_assessments"] - 1).clip(lower=1)
    a["assessment_index_frac"] = a["assessment_index"] / denom
    return a.rename(columns={"date": "assessment_date"})[
        [
            "id_assessment",
            "code_module",
            "code_presentation",
            "assessment_type",
            "weight",
            "assessment_date",
            "deadline",
            "assessment_index_frac",
            "module_n_assessments",
        ]
    ].rename(columns={"weight": "assessment_weight"})


# --------------------------------------------------------------------------- #
# Point-in-time features
# --------------------------------------------------------------------------- #


def _visible_mask(d: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """``M[i, j]``: attempt ``j`` is visible when predicting attempt ``i``.

    Visible means submitted strictly before ``i``'s prediction time and not
    ``i`` itself (an early submission of the target is still the target).
    """
    m = d[None, :] < pred[:, None]
    np.fill_diagonal(m, False)
    return m


def _prior_block(g: pd.DataFrame) -> pd.DataFrame:
    """Point-in-time aggregates for one student x module-presentation.

    ``g`` must be sorted by ``(date_submitted, id_assessment)``, so visible
    attempts keep submission order and the last visible attempt is the
    highest visible column.  Groups hold at most a few dozen attempts, so an
    explicit n x n visibility mask is cheap and easy to audit.
    """
    n = len(g)
    d = g["date_submitted"].to_numpy(dtype=float)
    s = g["score"].to_numpy(dtype=float)
    pred = g["prediction_time"].to_numpy(dtype=float)
    types = g["assessment_type"].to_numpy()
    deadline = g["deadline"].to_numpy(dtype=float)
    weight = g["assessment_weight"].to_numpy(dtype=float)

    m = _visible_mask(d, pred)
    mf = m.astype(float)
    k = mf.sum(axis=1)
    has = k > 0
    safe_k = np.maximum(k, 1.0)

    total = mf @ s
    mean = np.where(has, total / safe_k, np.nan)
    var = np.where(has, (mf @ (s * s)) / safe_k - mean**2, np.nan)
    std = np.sqrt(np.clip(var, 0.0, None))
    prior_min = np.where(has, np.where(m, s[None, :], np.inf).min(axis=1), np.nan)
    prior_max = np.where(has, np.where(m, s[None, :], -np.inf).max(axis=1), np.nan)

    idx = np.arange(n)
    last_j = np.where(m, idx[None, :], -1).max(axis=1)
    prev_j = np.where(m & (idx[None, :] < last_j[:, None]), idx[None, :], -1).max(axis=1)
    first_j = np.where(m, idx[None, :], n).min(axis=1)
    last = np.where(last_j >= 0, s[np.clip(last_j, 0, None)], np.nan)
    prev = np.where(prev_j >= 0, s[np.clip(prev_j, 0, None)], np.nan)
    delta_last2 = last - prev
    last_sub = np.where(last_j >= 0, d[np.clip(last_j, 0, None)], np.nan)
    first_sub = np.where(has, d[np.clip(first_j, 0, n - 1)], np.nan)

    wsum = mf @ weight
    weighted_mean = np.where(
        has,
        np.where(wsum > 0, (mf @ (weight * s)) / np.maximum(wsum, 1e-12), mean),
        np.nan,
    )

    # OLS slope of score against position (0..k-1) inside the visible history.
    pos = np.cumsum(mf, axis=1) - 1.0
    sx = (mf * pos).sum(axis=1)
    sxx = (mf * pos * pos).sum(axis=1)
    sxy = (mf * pos * s[None, :]).sum(axis=1)
    num = sxy - sx * total / safe_k
    den = sxx - sx**2 / safe_k
    slope = np.where((k > 1) & (den > 0), num / np.where(den > 0, den, 1.0), np.nan)

    # Same-assessment-type history (TMA / CMA / Exam); fall back to the overall mean.
    ms = (m & (types[None, :] == types[:, None])).astype(float)
    same_n = ms.sum(axis=1)
    same_mean = np.where(same_n > 0, (ms @ s) / np.maximum(same_n, 1.0), mean)

    # Submission timeliness of the visible history.
    late_days = d - deadline
    late_rate = np.where(has, (mf @ (late_days > 0).astype(float)) / safe_k, np.nan)
    mean_lateness = np.where(has, (mf @ np.maximum(late_days, 0.0)) / safe_k, np.nan)

    days_since_last = pred - last_sub
    mean_gap = np.where(k > 1, (last_sub - first_sub) / np.maximum(k - 1, 1.0), np.nan)

    return pd.DataFrame(
        {
            "prior_n": k,
            "prior_mean": mean,
            "prior_std": std,
            "prior_min": prior_min,
            "prior_max": prior_max,
            "prior_last": last,
            "prior_weighted_mean": weighted_mean,
            "prior_slope": slope,
            "prior_delta_last2": delta_last2,
            "prior_mean_same_type": same_mean,
            "prior_n_same_type": same_n,
            "prior_late_rate": late_rate,
            "prior_mean_lateness": mean_lateness,
            "days_since_last_sub": days_since_last,
            "prior_mean_gap": mean_gap,
            "last_prior_submission": last_sub,
        },
        index=g.index,
    )


def _cross_module_block(g: pd.DataFrame) -> pd.DataFrame:
    """History of the same student across *all* modules, point-in-time."""
    if len(g) == 0:
        return pd.DataFrame(columns=["prior_n_all", "prior_mean_all"], index=g.index)
    d = g["date_submitted"].to_numpy(dtype=float)
    s = g["score"].to_numpy(dtype=float)
    pred = g["prediction_time"].to_numpy(dtype=float)
    mf = _visible_mask(d, pred).astype(float)
    k = mf.sum(axis=1)
    mean = np.where(k > 0, (mf @ s) / np.maximum(k, 1.0), np.nan)
    return pd.DataFrame({"prior_n_all": k, "prior_mean_all": mean}, index=g.index)


def _vle_block(df: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    """Engagement features from daily VLE clicks strictly before ``prediction_time``.

    OULAD logs clicks server-side, so a day without a row genuinely had zero
    clicks (unlike a missing wearable reading).  Only "days since last click"
    is NaN, when there has been no click yet.
    """
    daily = daily.sort_values(ENROLMENT_KEY + ["date"], kind="mergesort").copy()
    group = daily.groupby(ENROLMENT_KEY, sort=False)
    daily["cum_clicks"] = group["sum_click"].cumsum().astype(float)
    daily["cum_days"] = (group.cumcount() + 1).astype(float)
    daily["date"] = daily["date"].astype(float)
    right = daily[ENROLMENT_KEY + ["date", "cum_clicks", "cum_days"]].sort_values("date", kind="mergesort")

    pred = df["prediction_time"].to_numpy(dtype=float)

    def as_of(t: np.ndarray) -> pd.DataFrame:
        left = df[ENROLMENT_KEY].copy()
        left["t"] = t
        left["row"] = np.arange(len(df))
        hit = pd.merge_asof(
            left.sort_values("t", kind="mergesort"),
            right,
            left_on="t",
            right_on="date",
            by=ENROLMENT_KEY,
            allow_exact_matches=False,  # strictly before t
            direction="backward",
        )
        return hit.sort_values("row").reset_index(drop=True)

    now, w7, w14 = as_of(pred), as_of(pred - 7.0), as_of(pred - 14.0)
    total = now["cum_clicks"].fillna(0.0).to_numpy()
    days = now["cum_days"].fillna(0.0).to_numpy()
    out = pd.DataFrame(
        {
            "vle_clicks_total": total,
            "vle_clicks_7d": total - w7["cum_clicks"].fillna(0.0).to_numpy(),
            "vle_clicks_14d": total - w14["cum_clicks"].fillna(0.0).to_numpy(),
            "vle_active_days_14d": days - w14["cum_days"].fillna(0.0).to_numpy(),
            "vle_days_since_last_click": pred - now["date"].to_numpy(dtype=float),
        },
        index=df.index,
    )
    return out


def build_features(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return one feature row per scored, non-banked attempt.

    Columns ending in ``_target`` / ``score`` / ``prediction_time`` are audit or
    label columns and are excluded from :data:`FEATURE_COLUMNS`.
    """
    df = clean_attempts(tables)
    if not {"deadline", "module_presentation_length"} <= set(df.columns):
        raise ValueError("tables are missing deadline metadata")

    # Fixed instant before the deadline: never depends on the target's own submission.
    df["prediction_time"] = df["deadline"] - PREDICTION_HORIZON_DAYS
    df["days_since_registration"] = df["prediction_time"] - df["date_registration"]
    df["unregistered_before_pred"] = (
        df["date_unregistration"].notna() & (df["date_unregistration"] < df["prediction_time"])
    ).astype(float)
    df["assessment_day"] = df["deadline"]
    df["imd_band"] = df["imd_band"].fillna("Unknown")

    df = df.sort_values(
        ["id_student", "code_module", "code_presentation", "date_submitted", "id_assessment"],
        kind="mergesort",
    ).reset_index(drop=True)
    df["rid"] = np.arange(len(df), dtype=np.int64)

    blocks = [
        _prior_block(g)
        for _, g in df.groupby(["id_student", "code_module", "code_presentation"], sort=False)
    ]
    history = pd.concat(blocks).sort_index()
    df = df.join(history)

    cross = [
        _cross_module_block(g)
        for _, g in df.groupby("id_student", sort=False)
    ]
    cross = pd.concat(cross).sort_index()
    df = df.join(cross)
    df["prior_other_n"] = df["prior_n_all"] - df["prior_n"]
    if "studentVle" in tables:
        df = df.join(_vle_block(df, tables["studentVle"]))

    # Keep the label last so accidental leakage is easy to spot.
    meta_columns = [
        "score",
        "id_student",
        "id_assessment",
        "code_module",
        "code_presentation",
        "date_submitted",
        "prediction_time",
        "last_prior_submission",
        "rid",
    ]
    ordered = FEATURE_COLUMNS + [c for c in meta_columns if c not in FEATURE_COLUMNS]
    extra = [c for c in df.columns if c not in ordered]
    return df[ordered + extra].sort_values("rid").reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Splits and audits
# --------------------------------------------------------------------------- #


def chronological_student_split(
    df: pd.DataFrame,
    train_presentations: tuple[str, ...] = TRAIN_PRESENTATIONS,
    val_presentations: tuple[str, ...] = VAL_PRESENTATIONS,
    test_presentations: tuple[str, ...] = TEST_PRESENTATIONS,
    min_prior: int = 1,
) -> dict:
    """Chronological presentation split with disjoint students.

    Presentations are ordered by calendar time (2013B < 2013J < 2014B < 2014J).
    A student appearing in an earlier split is removed from every later split,
    so train/val/test student sets are pairwise disjoint.  Rows without any
    visible prior attempt are not predictable by the score-history baselines
    and are dropped.
    """
    eligible = df[df["prior_n"] >= min_prior].copy()
    presentations = sorted(eligible["code_presentation"].unique())

    train = eligible[eligible["code_presentation"].isin(train_presentations)].copy()
    seen = set(train["id_student"])
    val_all = eligible[eligible["code_presentation"].isin(val_presentations)]
    val = val_all[~val_all["id_student"].isin(seen)].copy()
    seen |= set(val["id_student"])
    test_all = eligible[eligible["code_presentation"].isin(test_presentations)]
    test = test_all[~test_all["id_student"].isin(seen)].copy()

    splits = {"train": train, "val": val, "test": test}
    audit_rows = []
    all_students: set = set()
    for name, part in splits.items():
        students = set(part["id_student"])
        audit_rows.append(
            {
                "split": name,
                "presentations": ",".join(sorted(part["code_presentation"].unique())),
                "rows": len(part),
                "students": len(students),
                "student_overlap_with_earlier": len(students & all_students),
                "submission_min_day": float(part["date_submitted"].min()),
                "submission_max_day": float(part["date_submitted"].max()),
            }
        )
        all_students |= students
    audit = pd.DataFrame(audit_rows)
    overlap = {
        "train_val": len(set(train["id_student"]) & set(val["id_student"])),
        "train_test": len(set(train["id_student"]) & set(test["id_student"])),
        "val_test": len(set(val["id_student"]) & set(test["id_student"])),
    }
    return {
        "splits": splits,
        "audit": audit,
        "student_overlap": overlap,
        "presentation_order": presentations,
        "dropped": {
            "val_rows_overlapping_train_students": int(len(val_all) - len(val)),
            "test_rows_overlapping_earlier_students": int(len(test_all) - len(test)),
        },
    }


def audit_point_in_time(df: pd.DataFrame) -> dict:
    """Assertions that hold for a leak-free point-in-time feature table."""
    has_history = df["prior_n"] > 0
    violations = int(
        (
            has_history
            & df["last_prior_submission"].notna()
            & (df["last_prior_submission"] >= df["prediction_time"])
        ).sum()
    )

    forbidden = [
        c for c in FEATURE_COLUMNS if any(p in c.lower() for p in FORBIDDEN_FEATURE_PATTERNS)
    ]
    label_present = "score" in FEATURE_COLUMNS
    final_result_present = "final_result" in df.columns

    matrix = df[FEATURE_COLUMNS]
    numeric = matrix[NUMERIC_FEATURES].to_numpy(dtype=float)
    infinite_values = int(np.isinf(numeric).sum())
    nan_cells = int(np.isnan(numeric).sum())

    return {
        "rows": int(len(df)),
        "history_violations": violations,
        "target_score_in_features": bool(label_present),
        "final_result_in_frame": bool(final_result_present),
        "forbidden_feature_names": forbidden,
        "infinite_values": infinite_values,
        "nan_cells_imputed": nan_cells,
        "passed": (
            violations == 0
            and not label_present
            and not final_result_present
            and not forbidden
            and infinite_values == 0
        ),
    }


def spot_check_features(
    tables: dict[str, pd.DataFrame], df: pd.DataFrame, n_rows: int = 100, seed: int = 0
) -> dict:
    """Independently recompute prior_n / prior_mean / prior_last for sampled rows.

    Uses a naive explicit filter (not the cumulative-sum code path) to catch
    ordering, tie-handling, or group-key bugs.
    """
    attempts = clean_attempts(tables)
    rng = np.random.default_rng(seed)
    sample = df.iloc[rng.choice(len(df), size=min(n_rows, len(df)), replace=False)]
    max_n_diff = 0
    max_mean_diff = 0.0
    max_last_diff = 0.0
    for row in sample.itertuples(index=False):
        hist = attempts[
            (attempts["id_student"] == row.id_student)
            & (attempts["code_module"] == row.code_module)
            & (attempts["code_presentation"] == row.code_presentation)
            & (attempts["date_submitted"] < row.prediction_time)
            & (attempts["id_assessment"] != row.id_assessment)
        ]
        expected_n = float(len(hist))
        max_n_diff = max(max_n_diff, abs(expected_n - row.prior_n))
        if expected_n > 0:
            max_mean_diff = max(max_mean_diff, abs(hist["score"].mean() - row.prior_mean))
            last = hist.sort_values(["date_submitted", "id_assessment"]).iloc[-1]["score"]
            max_last_diff = max(max_last_diff, abs(last - row.prior_last))
    passed = max_n_diff == 0 and max_mean_diff < 1e-9 and max_last_diff < 1e-9
    return {
        "rows_checked": int(len(sample)),
        "max_prior_n_diff": max_n_diff,
        "max_prior_mean_diff": max_mean_diff,
        "max_prior_last_diff": max_last_diff,
        "passed": bool(passed),
    }


def future_invariance_check(
    tables: dict[str, pd.DataFrame], df: pd.DataFrame, keep_fraction: float = 0.6
) -> dict:
    """Strip future raw attempts and verify features of past rows do not move.

    For every student x module-presentation, keep only the first
    ``keep_fraction`` of attempts by submission date, rebuild the whole feature
    table, and compare it with the original on rows whose ``prediction_time``
    is at or before that enrollment's cutoff.  Any accidental use of future
    scores, cohort aggregates, or full-history statistics would change these
    values; a correct point-in-time implementation leaves them bit-identical.
    """
    sa = tables["studentAssessment"]
    meta = assessment_metadata(tables)
    temp = sa.merge(meta[["id_assessment", "code_module", "code_presentation"]], on="id_assessment", how="inner")
    temp = temp.sort_values(
        ["id_student", "date_submitted", "id_assessment"],
        kind="mergesort",
    )
    # Global per-student cutoff (not per enrolment): a student's past attempts
    # may sit in several module presentations, and cross-module history is a
    # legitimate feature.
    pos = temp.groupby("id_student", sort=False).cumcount()
    size = temp.groupby("id_student", sort=False)["id_assessment"].transform("size")
    cutoff_index = np.maximum((size * keep_fraction).astype(int) - 1, 0)
    kept = temp[pos <= cutoff_index].copy()

    cutoff_by_key = (
        kept.groupby("id_student", sort=False)["date_submitted"]
        .max()
        .rename("keep_cutoff")
        .reset_index()
    )
    truncated = dict(tables)
    truncated["studentAssessment"] = kept[sa.columns].copy()
    if "studentVle" in tables:
        # Drop each student's clicks after the same cutoff: VLE features must not move either.
        vle = tables["studentVle"].merge(cutoff_by_key, on="id_student", how="inner")
        truncated["studentVle"] = vle[vle["date"] <= vle["keep_cutoff"]].drop(columns="keep_cutoff")
    rebuilt = build_features(truncated)

    keys = ["id_student", "id_assessment"]
    compare = df.merge(
        rebuilt[keys + NUMERIC_FEATURES + CATEGORICAL_FEATURES],
        on=keys,
        suffixes=("", "_rebuilt"),
        how="inner",
    )
    # Only rows whose prediction instant is at or before the truncation
    # boundary are expected to be identical.
    compare = compare.merge(cutoff_by_key, on="id_student", how="left")
    comparable = compare[compare["prediction_time"] <= compare["keep_cutoff"]]

    max_num_diff = 0.0
    for col in NUMERIC_FEATURES:
        a = comparable[col].to_numpy(dtype=float)
        b = comparable[col + "_rebuilt"].to_numpy(dtype=float)
        both_nan = np.isnan(a) & np.isnan(b)
        diff = np.abs(a - b)
        diff[both_nan] = 0.0
        if np.isnan(diff).any():
            max_num_diff = float("inf")
            break
        max_num_diff = max(max_num_diff, float(np.nanmax(diff)) if len(diff) else 0.0)

    cat_equal = True
    for col in CATEGORICAL_FEATURES:
        a = comparable[col].fillna("__nan__").astype(str)
        b = comparable[col + "_rebuilt"].fillna("__nan__").astype(str)
        if not (a == b).all():
            cat_equal = False
            break

    return {
        "keep_fraction": keep_fraction,
        "rows_compared": int(len(comparable)),
        "max_numeric_abs_diff": max_num_diff,
        "categoricals_identical": bool(cat_equal),
        "passed": bool(max_num_diff < 1e-12 and cat_equal),
    }


# --------------------------------------------------------------------------- #
# Leakage probes
# --------------------------------------------------------------------------- #


def _design_matrix(
    train: pd.DataFrame, test: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray]:
    numeric = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False, min_frequency=10)),
        ]
    )
    pre = ColumnTransformer(
        [("num", numeric, NUMERIC_FEATURES), ("cat", categorical, CATEGORICAL_FEATURES)]
    )
    xtr = pre.fit_transform(train[FEATURE_COLUMNS])
    xte = pre.transform(test[FEATURE_COLUMNS])
    return np.asarray(xtr), np.asarray(xte)


def _probe_metrics(train: pd.DataFrame, test: pd.DataFrame, extra_train, extra_test) -> dict:
    xtr, xte = _design_matrix(train, test)
    extra_train = np.asarray(extra_train, dtype=float)
    extra_test = np.asarray(extra_test, dtype=float)
    fill = float(np.nanmedian(extra_train)) if np.isfinite(extra_train).any() else 0.0
    extra_train = np.where(np.isfinite(extra_train), extra_train, fill)
    extra_test = np.where(np.isfinite(extra_test), extra_test, fill)
    xtr = np.hstack([xtr, extra_train.reshape(-1, 1)])
    xte = np.hstack([xte, extra_test.reshape(-1, 1)])
    model = Ridge(alpha=1.0)
    model.fit(xtr, train["score"].to_numpy())
    pred = model.predict(xte)
    y = test["score"].to_numpy()
    err = pred - y
    ss_res = float(np.sum(err**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err**2))),
        "r2": float(1 - ss_res / ss_tot),
    }


def _future_mean_labels(df: pd.DataFrame) -> np.ndarray:
    """Mean score of same-enrollment attempts strictly after prediction_time.

    This is deliberately leaky and is only used as a negative control.
    """
    out = np.full(len(df), np.nan)
    for _, g in df.groupby(["id_student", "code_module", "code_presentation"], sort=False):
        order = np.argsort(g["date_submitted"].to_numpy(dtype=float), kind="mergesort")
        d = g["date_submitted"].to_numpy(dtype=float)[order]
        s = g["score"].to_numpy(dtype=float)[order]
        pred = g["prediction_time"].to_numpy(dtype=float)[order]
        suffix = np.concatenate((np.cumsum(s[::-1])[::-1], [0.0]))
        start = np.searchsorted(d, pred, side="right")
        count = len(d) - start
        mean_future = np.where(count > 0, suffix[start] / np.maximum(count, 1), np.nan)
        out[g.index.to_numpy()[order]] = mean_future
    return out


def run_leakage_suite(
    tables: dict[str, pd.DataFrame], df: pd.DataFrame, split: dict, n_spot_rows: int = 100
) -> dict:
    """Full leakage report: audits, invariance, and deliberately leaky probes."""
    splits = split["splits"]
    train, test = splits["train"], splits["test"]
    audit = audit_point_in_time(df)
    spot = spot_check_features(tables, df, n_rows=n_spot_rows)
    invariance = future_invariance_check(tables, df)
    overlap = split["student_overlap"]

    clean = _probe_metrics(train, test, np.zeros(len(train)), np.zeros(len(test)))
    target_probe = _probe_metrics(train, test, train["score"].to_numpy(), test["score"].to_numpy())
    future = _future_mean_labels(df)
    future_train = future[train.index.to_numpy()]
    future_test = future[test.index.to_numpy()]
    future_probe = _probe_metrics(train, test, future_train, future_test)

    # A probe is "caught" when it explains materially more variance than the
    # clean model, or reaches near-perfect accuracy.  The clean Ridge is the
    # reference; the margin is intentionally generous (0.10 R^2) so that only
    # real leakage trips it.
    r2_gain_target = target_probe["r2"] - clean["r2"]
    r2_gain_future = future_probe["r2"] - clean["r2"]
    target_flagged = target_probe["r2"] >= 0.99 or target_probe["mae"] < 0.5 * clean["mae"]
    future_flagged = future_probe["r2"] >= 0.95 or r2_gain_future >= 0.10

    probes = {
        "clean_reference": {**clean, "flagged": False, "r2_gain_over_clean": 0.0},
        "target_score_probe": {
            **target_probe,
            "flagged": bool(target_flagged),
            "r2_gain_over_clean": float(r2_gain_target),
        },
        "future_mean_probe": {
            **future_probe,
            "flagged": bool(future_flagged),
            "r2_gain_over_clean": float(r2_gain_future),
        },
    }

    passed = bool(
        audit["passed"]
        and spot["passed"]
        and invariance["passed"]
        and all(v == 0 for v in overlap.values())
        and probes["target_score_probe"]["flagged"]
        and probes["future_mean_probe"]["flagged"]
    )
    return {
        "audit": audit,
        "spot_check": spot,
        "future_invariance": invariance,
        "student_overlap": overlap,
        "probes": probes,
        "passed": passed,
    }


if __name__ == "__main__":  # quick self-check
    tables = load_oulad()
    frame = build_features(tables)
    split = chronological_student_split(frame)
    report = run_leakage_suite(tables, frame, split)
    print(report["audit"])
    print(report["spot_check"])
    print(report["future_invariance"])
    print(report["student_overlap"])
    for name, probe in report["probes"].items():
        print(name, probe)
    print("LEAKAGE SUITE PASSED:", report["passed"])
