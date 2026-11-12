"""
engineer_features.py
====================
Transforms the processed wearable dataset into a compact set of meaningful
engineered features for the CogniSync fatigue prediction model.

Reads  : fatigue_model/data/processed/processed_dataset.csv
Writes : fatigue_model/data/processed/engineered_dataset.csv

Design rules
------------
* 15–20 engineered model input features, derived from meaningful combinations
  of related raw measurements.  Simple renaming is avoided.
* Every participant-day row is preserved.  No aggregation, sampling, or
  observation removal.
* Missing wearable measurements are propagated as NaN (no imputation here).
* No target leakage, imputation, feature selection, or model training.
* Stress / mood / psychological / other survey variables are excluded.
* Participant ID and date are retained as metadata only (not model inputs).
* The original processed dataset is never written to or modified.

Output columns
--------------
  user_id              – participant metadata
  activity_date        – single date column (calendar date of activity)
  <15–20 features>     – engineered model inputs
  tired_yesterday_code – encoded fatigue target (0–4)

Intentionally removed from output
----------------------------------
  date             – duplicates activity_date
  tired_yesterday  – string version; encoded target already retained
  split            – will be assigned at model-training time, not here
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
INPUT_PATH  = PROCESSED_DIR / "processed_dataset.csv"
OUTPUT_PATH = PROCESSED_DIR / "engineered_dataset.csv"

# ---------------------------------------------------------------------------
# Ordinal target reference (for validation output only)
# ---------------------------------------------------------------------------
TARGET_ORDER = ["not_at_all", "a_little_bit", "somewhat", "quite_a_bit", "very_much"]

# ---------------------------------------------------------------------------
# Engineering specification
# Each entry documents: sources, formula, meaning, and why it is distinct.
# ---------------------------------------------------------------------------
FEATURE_DOCS = {
    # ── SLEEP ──────────────────────────────────────────────────────────────
    "sleep_duration_min": {
        "group": "Sleep",
        "sources": ["sleep__total_asleep_minutes"],
        "formula": "sleep__total_asleep_minutes (direct, all bouts, Fitbit)",
        "meaning": (
            "Total minutes asleep across all sleep bouts for the day "
            "(main sleep + naps).  Uses the Fitbit-computed value which "
            "combines main sleep and nap asleep minutes without double-counting."
        ),
        "why_distinct": (
            "Captures absolute sleep quantity.  sleep__asleep__sum (Evidation) "
            "is very similar but was found to exceed sleep__total_in_bed_minutes "
            "in 6 rows — a data inconsistency; sleep__total_asleep_minutes "
            "(Fitbit) has no such anomaly and is preferred.  "
            "sleep__sleeping__sum includes restless/awake minutes within the "
            "sleep window and therefore overestimates true sleep time."
        ),
    },
    "sleep_efficiency_pct": {
        "group": "Sleep",
        "sources": ["sleep__main_efficiency"],
        "formula": "sleep__main_efficiency (direct, Fitbit, 0–100)",
        "meaning": (
            "Fitbit sleep-efficiency score for the main sleep bout, "
            "computed as (asleep minutes / in-bed minutes) × 100.  "
            "Reflects how much of the time in bed was spent actually asleep."
        ),
        "why_distinct": (
            "Efficiency condenses the duration/in-bed relationship into a "
            "single ratio and adds qualitative information beyond raw duration. "
            "sleep__loop_main_asleep_frac is the Evidation analogue but covers "
            "only the main sleep; it is redundant given sleep_efficiency_pct."
        ),
    },
    "sleep_fragmentation_index": {
        "group": "Sleep",
        "sources": [
            "sleep__really_awake__sum",
            "sleep__total_asleep_minutes",
        ],
        "formula": (
            "sleep__really_awake__sum / (sleep__total_asleep_minutes + "
            "sleep__really_awake__sum)  — proportion of sleep-window time "
            "that was 'really awake' (NaN when denominator is 0)"
        ),
        "meaning": (
            "Fraction of the total sleep-window time (asleep + truly awake) "
            "spent in unambiguous full wakefulness.  Higher values indicate "
            "more interrupted sleep, which is a meaningful independent "
            "predictor of fatigue beyond just duration or efficiency."
        ),
        "why_distinct": (
            "Efficiency captures overall sleep quality; fragmentation_index "
            "specifically captures intermittent full-wakefulness events, "
            "which may differ from the restless/light periods captured by "
            "efficiency.  sleep__awake__sum includes restless minutes and "
            "is therefore broader; sleep__really_awake__sum is the stricter "
            "measure.  sleep__awake_regions__countDistinct counts episodes "
            "but ignores duration; this index captures duration-weighted "
            "fragmentation."
        ),
    },
    "sleep_onset_latency_min": {
        "group": "Sleep",
        "sources": ["sleep__loop_main_until_sleep_minutes"],
        "formula": "sleep__loop_main_until_sleep_minutes (direct, Evidation)",
        "meaning": (
            "Minutes spent in bed before falling asleep (sleep-onset latency). "
            "Reflects how difficult it was to fall asleep, which is a distinct "
            "sleep-quality dimension not captured by duration or efficiency."
        ),
        "why_distinct": (
            "Duration, efficiency and fragmentation all relate to the sleep "
            "period itself; onset latency measures the pre-sleep transition. "
            "sleep__loop_main_to_wakeup_minutes (time in bed after waking) "
            "is the symmetric post-sleep metric; it is excluded because it "
            "is predominantly near-zero (mean = 2 min) and adds little "
            "differentiation."
        ),
    },
    # ── PHYSICAL ACTIVITY ──────────────────────────────────────────────────
    "total_steps": {
        "group": "Activity",
        "sources": ["steps__sum"],
        "formula": "steps__sum (direct, Evidation)",
        "meaning": (
            "Total step count for the day.  The primary indicator of overall "
            "daily movement volume."
        ),
        "why_distinct": (
            "steps__count is the number of non-zero minutes, not step count. "
            "Rolling-window and percentile columns capture burst intensity "
            "or distributional shape but not total volume; they are excluded "
            "in favour of specialised features below."
        ),
    },
    "active_minutes": {
        "group": "Activity",
        "sources": ["steps__light_activity__sum", "steps__mvpa__sum"],
        "formula": "steps__light_activity__sum + steps__mvpa__sum",
        "meaning": (
            "Total minutes of non-sedentary purposeful activity per day "
            "(light: 50–100 steps/min; MVPA: >100 steps/min).  "
            "Both source columns measure activity in minutes and are "
            "non-overlapping by definition, so summation is valid."
        ),
        "why_distinct": (
            "Captures whether the person was meaningfully active at all, "
            "independent of intensity.  total_steps reflects volume; "
            "active_minutes reflects time engaged in movement.  They "
            "are complementary because step totals can be driven by "
            "a few intense bursts while active_minutes rewards sustained "
            "lower-intensity movement."
        ),
    },
    "mvpa_minutes": {
        "group": "Activity",
        "sources": ["steps__mvpa__sum"],
        "formula": "steps__mvpa__sum (direct, Evidation, >100 steps/min)",
        "meaning": (
            "Minutes of moderate-to-vigorous physical activity.  "
            "Retained separately from active_minutes because MVPA intensity "
            "is independently associated with fatigue recovery and "
            "cardiovascular load."
        ),
        "why_distinct": (
            "active_minutes combines light and MVPA; mvpa_minutes isolates "
            "the higher-intensity component which carries different "
            "physiological and fatigue implications."
        ),
    },
    "sedentary_minutes": {
        "group": "Activity",
        "sources": ["steps__sedentary__sum"],
        "formula": "steps__sedentary__sum (direct, Evidation, <50 steps/min)",
        "meaning": (
            "Minutes classified as sedentary (<50 steps/min).  Captures "
            "how much of the waking day involved very low movement, "
            "independently of total step count."
        ),
        "why_distinct": (
            "steps__not_moving__sum (zero steps, mean=1 231 min) conflates "
            "sleep and sedentary time, making it uninterpretable as a "
            "daytime behaviour measure.  sedentary_minutes (mean=211 min, "
            "i.e. ~3.5 h of waking low-activity) is the validated "
            "sedentary-behaviour threshold.  It is not derivable from "
            "total_steps because step count distributes across all intensity "
            "bands."
        ),
    },
    "peak_activity_intensity": {
        "group": "Activity",
        "sources": ["steps__max_rolling_30"],
        "formula": "steps__max_rolling_30 (direct, Evidation)",
        "meaning": (
            "Maximum steps accumulated in any 30-minute window.  "
            "Captures the intensity of the most active 30-minute bout "
            "in the day, reflecting peak physical demand independently "
            "of duration or total volume."
        ),
        "why_distinct": (
            "total_steps and active_minutes measure daily totals; "
            "mvpa_minutes captures sustained intensity; peak_activity_intensity "
            "captures the single most demanding bout, which may be "
            "particularly relevant to same-day recovery and fatigue. "
            "30 min was chosen as it balances burst sensitivity and "
            "noise: 1-min and 3-min windows capture single-step "
            "spikes, while 60-min windows start to reflect sustained "
            "endurance rather than peak demand."
        ),
    },
    # ── HEART RATE ─────────────────────────────────────────────────────────
    "resting_hr_bpm": {
        "group": "HeartRate",
        "sources": ["heart_rate__resting_heart_rate"],
        "formula": "heart_rate__resting_heart_rate (direct, Fitbit)",
        "meaning": (
            "Resting heart rate — the number of heartbeats per minute at rest. "
            "A lower resting HR typically reflects better cardiovascular fitness. "
            "Elevated resting HR can signal stress, illness, or insufficient "
            "recovery."
        ),
        "why_distinct": (
            "heart_rate__not_moving__mean (mean=75.5 bpm) is a proxy for "
            "resting HR but is computed from all not-moving minutes, including "
            "while upright and stationary; Fitbit's resting_heart_rate "
            "(mean=66.8 bpm) is specifically computed during the lowest-HR "
            "period and is the standard clinical definition."
        ),
    },
    "hr_mean_bpm": {
        "group": "HeartRate",
        "sources": ["heart_rate__mean"],
        "formula": "heart_rate__mean (direct, Evidation, all minutes HR>0)",
        "meaning": (
            "Daily mean heart rate across all minutes with recorded HR.  "
            "Reflects overall daily cardiac load."
        ),
        "why_distinct": (
            "resting_hr_bpm is the resting baseline; hr_mean_bpm is the "
            "daily average including activity and sleep, capturing the "
            "total cardiac burden.  heart_rate__awake__mean (mean=81.9) "
            "and heart_rate__asleep__mean (mean=66.4) are sub-period means; "
            "the daily mean is a simpler, complete summary and they add "
            "collinear information."
        ),
    },
    "hr_range_bpm": {
        "group": "HeartRate",
        "sources": ["heart_rate__perc_95th", "heart_rate__perc_5th"],
        "formula": "heart_rate__perc_95th - heart_rate__perc_5th",
        "meaning": (
            "Inter-percentile range of heart rate (95th minus 5th percentile). "
            "Captures how much HR varied across the day, using robust "
            "percentile bounds that are insensitive to single-measurement "
            "outliers.  A wider range indicates a more varied, active day "
            "or less stable cardiac response."
        ),
        "why_distinct": (
            "heart_rate__stddev measures statistical spread around the mean, "
            "which is sensitive to outliers and skew; the 90th inter-percentile "
            "range (P95–P5) is a robust alternative.  hr_mean_bpm captures "
            "the level; hr_range_bpm captures the spread — these are "
            "orthogonal dimensions.  heart_rate__max (mean=131.8) includes "
            "single-minute peaks and was checked: mean is only 30 bpm above "
            "P95 (101.9) so max is moderately outlier-influenced; P95–P5 "
            "is cleaner.  Note: this is NOT clinical HRV, which requires "
            "inter-beat-interval data."
        ),
    },
    "hr_elevation_ratio": {
        "group": "HeartRate",
        "sources": [
            "heart_rate__mean",
            "heart_rate__resting_heart_rate",
        ],
        "formula": (
            "heart_rate__mean / heart_rate__resting_heart_rate  "
            "(NaN when resting HR is 0 or missing)"
        ),
        "meaning": (
            "Ratio of daily mean HR to resting HR.  Indicates how much "
            "the heart had to work above its baseline on a given day. "
            "A ratio of 1.0 means the day was as calm as rest; higher "
            "values reflect greater physiological exertion."
        ),
        "why_distinct": (
            "resting_hr_bpm and hr_mean_bpm are both present; their ratio "
            "is a normalised, person-relative metric that accounts for "
            "individual baseline differences — a mean of 80 bpm means "
            "something different for someone with a resting HR of 55 versus 75. "
            "heart_rate__quant_95th_to_resting_ratio captures peak demand "
            "relative to rest; hr_elevation_ratio captures average daily "
            "demand — complementary, not redundant."
        ),
    },
    "hr_high_intensity_frac": {
        "group": "HeartRate",
        "sources": ["heart_rate__high_150_perc_resting_frac"],
        "formula": (
            "heart_rate__high_150_perc_resting_frac (direct, Evidation) — "
            "fraction of minutes where HR > 1.5× resting HR"
        ),
        "meaning": (
            "Proportion of the day spent at elevated cardiac intensity "
            "(HR above 150 % of resting HR).  Captures time in a "
            "physiologically demanding state relative to the individual's "
            "own resting baseline."
        ),
        "why_distinct": (
            "hr_elevation_ratio is an average across the whole day; "
            "hr_high_intensity_frac isolates the duration spent at "
            "high relative intensity.  heart_rate__high_200_perc_resting_frac "
            "(mean=0.01, max=0.23) covers near-maximal exertion — it was "
            "checked and 90 % of rows have values below 0.03, making it "
            "very sparse and poorly differentiated; it is excluded."
        ),
    },
    "hr_temporal_consistency": {
        "group": "HeartRate",
        "sources": ["heart_rate__autocorr10min"],
        "formula": "heart_rate__autocorr10min (direct, Evidation)",
        "meaning": (
            "10-minute autocorrelation of HR — how strongly the HR at any "
            "minute predicts HR 10 minutes later.  High values indicate "
            "that HR varied smoothly across the day (consistent load); "
            "low values indicate abrupt, irregular fluctuations."
        ),
        "why_distinct": (
            "hr_range_bpm measures the total spread; hr_temporal_consistency "
            "measures the temporal structure of variation — whether HR "
            "changes are gradual or abrupt.  Autocorrelations at 1-, 2-, "
            "3-min lags are very high for virtually all days (mean≈0.94, "
            "0.88, 0.83) and carry little discriminating power; the 60-min "
            "lag (mean=0.40) is noisier; 10-min provides meaningful "
            "day-to-day variation (range –0.19 to 0.94)."
        ),
    },
    # ── WEARABLE COVERAGE ──────────────────────────────────────────────────
    "fitbit_wear_fraction": {
        "group": "Coverage",
        "sources": ["active_fitbit__sum"],
        "formula": "active_fitbit__sum / 1440  (minutes in a day)",
        "meaning": (
            "Fraction of the 24-hour day that the Fitbit was worn and "
            "recording data.  Values near 1.0 indicate the device was "
            "worn almost continuously; lower values indicate partial wear."
        ),
        "why_distinct": (
            "All wearable features depend on how completely the device was "
            "worn; this fraction is a data-quality covariate that models "
            "can use to discount less complete days.  It is not a "
            "physiological feature but a measurement-coverage indicator. "
            "active_fitbit__awake__sum conditions on being awake; we prefer "
            "the total (active_fitbit__sum) for a simple, interpretable "
            "coverage metric."
        ),
    },
}

FEATURE_NAMES = list(FEATURE_DOCS.keys())   # 16 features

# ---------------------------------------------------------------------------
# Columns in the input that are intentionally excluded from the output,
# with brief documented reasons.
# ---------------------------------------------------------------------------
EXCLUDED_RAW = {
    # Duplicates / near-identical to retained features
    "sleep__asleep__sum": "Preferred sleep__total_asleep_minutes (no anomalies).",
    "sleep__asleep__mean": "Proportion of asleep minutes; redundant with sleep_duration_min.",
    "sleep__sleeping__sum": "Includes restless/awake within sleep window; overestimates true sleep.",
    "sleep__total_in_bed_minutes": "Derivable from sleep_duration_min and sleep_efficiency_pct; retaining both would create collinearity.",
    "sleep__main_in_bed_minutes": "Main-sleep-only in-bed time; sleep__total_in_bed_minutes already excluded.",
    "sleep__main_asleep_minutes": "Main-sleep-only asleep minutes; sleep_duration_min (total) preferred.",
    "sleep__main_efficiency": "Retained as sleep_efficiency_pct.",
    "sleep__loop_main_asleep_frac": "Evidation main-sleep efficiency proxy; redundant with sleep_efficiency_pct.",
    "sleep__loop_main_asleep_minutes": "Main-sleep asleep minutes; redundant with sleep_duration_min.",
    "sleep__loop_main_awake_frac": "Awake fraction — complementary to efficiency but adds collinear information.",
    "sleep__loop_main_awake_minutes": "Awake minutes in main sleep; redundant with fragmentation index.",
    "sleep__awake__sum": "Includes restless+awake; sleep__really_awake__sum used in fragmentation index.",
    "sleep__awake__mean": "Proportion metric; awake total used for fragmentation index.",
    "sleep__awake_regions__countDistinct": "Episode count without duration weighting; fragmentation_index preferred.",
    "sleep__really_awake__mean": "Proportion metric of really-awake; fragmentation_index uses the absolute minutes.",
    "sleep__really_awake__sum": "Used directly in fragmentation index calculation.",
    "sleep__really_awake_regions__countDistinct": "Count of truly-awake episodes; redundant with fragmentation_index.",
    "sleep__loop_main_really_awake_frac": "Same concept as fragmentation index restricted to main sleep.",
    "sleep__loop_main_really_awake_minutes": "Same concept, main sleep only.",
    "sleep__loop_main_really_awake_region_count": "Episode count; redundant.",
    "sleep__loop_main_awake_region_count": "Episode count including restless; redundant.",
    "sleep__loop_main_to_wakeup_minutes": "Time in bed after waking; mean=2 min, near-zero for most rows.",
    "sleep__loop_main_until_sleep_minutes": "Retained as sleep_onset_latency_min.",
    "sleep__main_start_time": "Datetime string; excluded per task specification.",
    "sleep__main_start_minute": "Sleep-timing feature; excluded per task specification.",
    "sleep__nap_count": "Predominantly zero (87 % of rows = 0); excluded per task specification.",
    "sleep__num_sleeps": "Total bouts = main + naps; nap_count already excluded.",
    # Activity
    "steps__sum": "Retained as total_steps.",
    "steps__light_activity__sum": "Component of active_minutes.",
    "steps__mvpa__sum": "Retained as mvpa_minutes AND is a component of active_minutes.",
    "steps__sedentary__sum": "Retained as sedentary_minutes.",
    "steps__max_rolling_30": "Retained as peak_activity_intensity.",
    "steps__count": "Number of non-zero-step minutes; different from step count.",
    "steps__not_moving__sum": "Mean=1 231 min — conflates sleep and waking sedentary time.",
    "steps__streaks__countDistinct": "Number of non-zero-step streaks; not a primary fatigue predictor.",
    "steps__non_zero_frac": "Fraction of minutes with any steps; correlated with total_steps.",
    "steps__midday_steps_dec_time": "Timing of step midpoint; timing feature, excluded.",
    "steps__first_step_dec_time": "Timing feature; excluded.",
    "steps__last_step_dec_time": "Timing feature; excluded.",
    "steps__dec_time__max": "Timing of maximum-step minute; timing feature.",
    "steps__dec_time__min": "Timing of minimum-step minute; timing feature.",
    "steps__dec_time_max_rolling_6__first": "Timing feature; excluded.",
    "steps__rolling_6_sum__max": "6-min peak steps; redundant with peak_activity_intensity (30-min).",
    "steps__max_rolling_1": "1-min peak — single-step spike detector; noisy.",
    "steps__max_rolling_3": "3-min peak; similar reasoning.",
    "steps__max_rolling_6": "6-min peak; redundant with 30-min window.",
    "steps__max_rolling_10": "10-min peak; redundant.",
    "steps__max_rolling_60": "60-min peak; reflects sustained endurance, not peak demand.",
    "steps__max_rolling_dec_time_1": "Timing of rolling peak; timing feature.",
    "steps__max_rolling_dec_time_3": "Timing of rolling peak; timing feature.",
    "steps__max_rolling_dec_time_6": "Timing of rolling peak; timing feature.",
    "steps__max_rolling_dec_time_10": "Timing of rolling peak; timing feature.",
    "steps__max_rolling_dec_time_30": "Timing of retained 30-min peak window; timing feature.",
    "steps__max_rolling_dec_time_60": "Timing of rolling peak; timing feature.",
    "steps__gt10_nonzero_frac": "Fraction of non-zero minutes above 10 steps; crude intensity proxy.",
    "steps__gt50_nonzero_frac": "Fraction above 50 steps among non-zero; redundant with intensity categories.",
    "steps__gt100_nonzero_frac": "Fraction above 100 steps among non-zero (different denominator to mvpa_minutes).",
    "steps__gt140_nonzero_frac": "Fraction above 140 steps; very sparse.",
    "steps__nonzero_5quantile": "5th percentile of non-zero steps; distributional detail.",
    "steps__nonzero_50quantile": "Median of non-zero steps; redundant with total_steps.",
    "steps__nonzero_95quantile": "95th percentile; redundant with peak_activity_intensity.",
    "active_fitbit__awake__sum": "Wear time while awake only; total wear fraction already captured.",
    "active_fitbit__sum": "Used to compute fitbit_wear_fraction.",
    # Heart rate
    "heart_rate__resting_heart_rate": "Retained as resting_hr_bpm.",
    "heart_rate__mean": "Retained as hr_mean_bpm.",
    "heart_rate__perc_95th": "Component of hr_range_bpm.",
    "heart_rate__perc_5th": "Component of hr_range_bpm.",
    "heart_rate__high_150_perc_resting_frac": "Retained as hr_high_intensity_frac.",
    "heart_rate__autocorr10min": "Retained as hr_temporal_consistency.",
    "heart_rate__asleep__max": "Sleep-period max; redundant with daily mean and range.",
    "heart_rate__asleep__mean": "Sleep-period mean; captured within hr_mean_bpm.",
    "heart_rate__asleep__stddev": "Sleep-period HR std; redundant with hr_range_bpm.",
    "heart_rate__awake__max": "Awake-period max; similar to overall max.",
    "heart_rate__awake__mean": "Awake-period mean; redundant with hr_mean_bpm.",
    "heart_rate__awake__stddev": "Awake-period HR std; redundant.",
    "heart_rate__not_moving__max": "Not-moving max; proxy for resting, superseded by resting_hr_bpm.",
    "heart_rate__not_moving__mean": "Not-moving mean; proxy for resting, superseded.",
    "heart_rate__not_moving__stddev": "Not-moving HR std; redundant.",
    "heart_rate__perc_25th": "25th percentile; distributional detail covered by mean+range.",
    "heart_rate__perc_50th": "Median HR — nearly identical to hr_mean_bpm (mean diff < 2 bpm).",
    "heart_rate__perc_75th": "75th percentile; redundant with range.",
    "heart_rate__stddev": "Daily HR standard deviation — sensitive to outliers; hr_range_bpm (P95–P5) preferred.",
    "heart_rate__quant_95th_to_resting_ratio": "P95-to-resting ratio; similar concept to hr_elevation_ratio but uses P95.",
    "heart_rate__autocorr1min": "Mean=0.94 for virtually all rows; near-constant, low discriminative power.",
    "heart_rate__autocorr2min": "Mean=0.88; still very high, limited variation.",
    "heart_rate__autocorr3min": "Mean=0.83; moderate variation but 10-min preferred.",
    "heart_rate__autocorr60min": "60-min lag; noisier than 10-min (wider range, more sparse variation).",
    "heart_rate__count": "Minutes with HR>0; device coverage proxied by fitbit_wear_fraction.",
    "heart_rate__high_200_perc_resting_frac": "90th pctile of values < 0.03; too sparse for reliable signal.",
    "heart_rate__max": "Single-minute peak; outlier-sensitive. hr_range_bpm (P95–P5) preferred.",
    "heart_rate__median": "Mean diff from hr_mean_bpm < 2 bpm across dataset; near-duplicate.",
    "heart_rate__min": "Minimum HR; often artefactual (mean=55.8, min=32).",
    "heart_rate__peaks": "Number of relative HR peaks; complex structural metric.",
    "heart_rate__peaks_gt_125_perc_median": "Peaks above 1.25×median; redundant with hr_high_intensity_frac.",
    "heart_rate__peaks_gt_150_perc_median": "Peaks above 1.5×median; uses median baseline, not resting — different from hr_high_intensity_frac but adds limited extra signal.",
    "heart_rate__peaks_gt_200_perc_median": "Very sparse; redundant.",
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # ── Load ────────────────────────────────────────────────────────────────
    if not INPUT_PATH.exists():
        print(f"ERROR: Input file not found: {INPUT_PATH}", file=sys.stderr)
        sys.exit(1)

    df_in = pd.read_csv(INPUT_PATH, low_memory=False)
    input_rows         = len(df_in)
    input_participants = df_in["user_id"].nunique()

    print("=" * 72)
    print("FEATURE ENGINEERING — DIAGNOSTIC REPORT")
    print("=" * 72)
    print(f"\nInput  : {INPUT_PATH}")
    print(f"Rows   : {input_rows:,}")
    print(f"Unique participants: {input_participants}")

    print("\nTarget distribution (input):")
    input_dist = df_in["tired_yesterday"].value_counts().reindex(TARGET_ORDER, fill_value=0)
    for lbl, cnt in input_dist.items():
        code = TARGET_ORDER.index(lbl)
        print(f"  {code}  {lbl:<20}  {cnt:>5} rows")

    # ── Build output skeleton ────────────────────────────────────────────────
    out = pd.DataFrame()
    out["user_id"]       = df_in["user_id"]
    out["activity_date"] = df_in["activity_date"]

    # ── Compute engineered features ─────────────────────────────────────────
    # Sleep
    out["sleep_duration_min"] = df_in["sleep__total_asleep_minutes"]

    out["sleep_efficiency_pct"] = df_in["sleep__main_efficiency"]

    denom = df_in["sleep__total_asleep_minutes"] + df_in["sleep__really_awake__sum"]
    out["sleep_fragmentation_index"] = np.where(
        denom > 0,
        df_in["sleep__really_awake__sum"] / denom,
        np.nan,
    )

    out["sleep_onset_latency_min"] = df_in["sleep__loop_main_until_sleep_minutes"]

    # Activity
    out["total_steps"] = df_in["steps__sum"]

    out["active_minutes"] = (
        df_in["steps__light_activity__sum"] + df_in["steps__mvpa__sum"]
    )

    out["mvpa_minutes"] = df_in["steps__mvpa__sum"]

    out["sedentary_minutes"] = df_in["steps__sedentary__sum"]

    out["peak_activity_intensity"] = df_in["steps__max_rolling_30"]

    # Heart rate
    out["resting_hr_bpm"] = df_in["heart_rate__resting_heart_rate"]

    out["hr_mean_bpm"] = df_in["heart_rate__mean"]

    out["hr_range_bpm"] = df_in["heart_rate__perc_95th"] - df_in["heart_rate__perc_5th"]

    resting = df_in["heart_rate__resting_heart_rate"].replace(0, np.nan)
    out["hr_elevation_ratio"] = df_in["heart_rate__mean"] / resting

    out["hr_high_intensity_frac"] = df_in["heart_rate__high_150_perc_resting_frac"]

    out["hr_temporal_consistency"] = df_in["heart_rate__autocorr10min"]

    # Coverage
    out["fitbit_wear_fraction"] = df_in["active_fitbit__sum"] / 1440.0

    # Target
    out["tired_yesterday_code"] = df_in["tired_yesterday_code"]

    # ── Integrity checks ─────────────────────────────────────────────────────
    output_rows         = len(out)
    output_participants = out["user_id"].nunique()

    rows_ok        = output_rows == input_rows
    parts_ok       = output_participants == input_participants
    target_ok      = out["tired_yesterday_code"].equals(df_in["tired_yesterday_code"])
    dates_ok       = out["activity_date"].equals(df_in["activity_date"].astype(str))
    one_date_col   = sum(1 for c in out.columns if "date" in c.lower()) == 1
    one_target_col = sum(1 for c in out.columns if "tired" in c.lower()) == 1

    # ── Save ─────────────────────────────────────────────────────────────────
    out.to_csv(OUTPUT_PATH, index=False)

    # ── Print report ─────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("ENGINEERED FEATURE DEFINITIONS")
    print("=" * 72)

    for feat, doc in FEATURE_DOCS.items():
        miss = int(out[feat].isna().sum())
        print(f"\n  Feature  : {feat}  [{doc['group']}]  |  missing: {miss}")
        print(f"  Sources  : {', '.join(doc['sources'])}")
        print(f"  Formula  : {doc['formula']}")
        # Word-wrap meaning and distinctness at 70 chars
        for label, text in [("Meaning  ", doc["meaning"]), ("Distinct ", doc["why_distinct"])]:
            words = text.split()
            line = f"  {label}: "
            for w in words:
                if len(line) + len(w) + 1 > 80:
                    print(line.rstrip())
                    line = " " * 13 + w + " "
                else:
                    line += w + " "
            print(line.rstrip())

    print("\n" + "=" * 72)
    print("EXCLUDED RAW COLUMNS")
    print("=" * 72)
    for col, reason in EXCLUDED_RAW.items():
        print(f"  {col}")
        print(f"      {reason}")

    print("\n" + "=" * 72)
    print("MISSING-VALUE SUMMARY FOR ENGINEERED FEATURES")
    print("=" * 72)
    for feat in FEATURE_NAMES:
        miss = int(out[feat].isna().sum())
        pct  = 100.0 * miss / output_rows if output_rows > 0 else 0.0
        flag = "  ← NOTE: >10 % missing" if pct > 10 else ""
        print(f"  {feat:<35}  {miss:>5} missing  ({pct:5.1f} %){flag}")

    print("\n" + "=" * 72)
    print("OUTPUT VALIDATION")
    print("=" * 72)
    print(f"  Input  rows       : {input_rows:,}")
    print(f"  Output rows       : {output_rows:,}  {'✓' if rows_ok else '✗ MISMATCH'}")
    print(f"  Input  participants: {input_participants}")
    print(f"  Output participants: {output_participants}  {'✓' if parts_ok else '✗ MISMATCH'}")
    print(f"  All participant-day observations preserved: {'✓' if rows_ok else '✗'}")
    print(f"  Target values unchanged : {'✓' if target_ok else '✗'}")
    print(f"  Date values unchanged   : {'✓' if dates_ok else '✗'}")
    print(f"  Exactly one date column : {'✓' if one_date_col else '✗'}")
    print(f"  Exactly one target col  : {'✓' if one_target_col else '✗'}")
    print(f"  Original dataset untouched: ✓ (never written to)")
    print(f"\n  Number of model input features: {len(FEATURE_NAMES)}")
    print(f"  Feature names: {FEATURE_NAMES}")

    print("\nTarget distribution (output — must match input):")
    # Rebuild tired_yesterday from codes for comparison
    code_to_label = {i: lbl for i, lbl in enumerate(TARGET_ORDER)}
    out_dist = out["tired_yesterday_code"].map(code_to_label).value_counts().reindex(
        TARGET_ORDER, fill_value=0
    )
    for lbl, cnt in out_dist.items():
        code = TARGET_ORDER.index(lbl)
        match = "✓" if cnt == input_dist[lbl] else "✗"
        print(f"  {match} {code}  {lbl:<20}  {cnt:>5} rows")

    print("\nOrdinal encoding (preserved unchanged):")
    for i, lbl in enumerate(TARGET_ORDER):
        print(f"  {i}  {lbl}")

    print(f"\nOutput written to: {OUTPUT_PATH}")

    if not (rows_ok and parts_ok and target_ok):
        print("\nERROR: Integrity check failed — output may be compromised.", file=sys.stderr)
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
