'''Preprocessing script for the Zenodo wearable dataset used by the CogniSync fatigue estimation model.

The script follows the specifications given in the user request:
* Loads the four raw CSV files located in ``data/raw``.
* Uses the column names and semantics described in the two data‑dictionary files.
* Identifies the participant identifier (``user_id``), the activity date (``date``) and the
  survey timestamps (``one_click_submitted_datetime`` / ``survey_start_datetime``).
* Joins each fatigue survey response (``tired_yesterday``) with the activity record from the
  **previous** calendar day (the survey asks about *yesterday*).
* Keeps only the required feature groups – sleep, physical activity and heart‑rate – and
  discards all stress‑related / mood‑related fields.
* Handles missing values by simple imputation (numeric → median, categorical → most frequent).
* Encodes the ordered fatigue target preserving its ordinal nature.
* Stores the final tidy table in ``data/processed/processed_dataset.csv`` and leaves participant
  identifiers separate for later train/test splitting.
''' 

import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to project root)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]  # fatigue_model directory
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Load raw files
# ---------------------------------------------------------------------------
activity_path = RAW_DIR / "day_activity_features.csv"
survey_path = RAW_DIR / "daily_surveys_one_click_responses.csv"
activity_dict_path = RAW_DIR / "activity_feature_data_dictionary.csv"
survey_dict_path = RAW_DIR / "daily_survey_data_dictionary.csv"

activity_df = pd.read_csv(activity_path)
# Ensure activity date is a datetime.date for proper join
activity_df["date"] = pd.to_datetime(activity_df["date"]).dt.date
survey_df = pd.read_csv(survey_path)
activity_dict = pd.read_csv(activity_dict_path)
survey_dict = pd.read_csv(survey_dict_path)

# ---------------------------------------------------------------------------
# Identify key columns
# ---------------------------------------------------------------------------
PARTICIPANT_COL = "user_id"
ACTIVITY_DATE_COL = "date"
# Survey timestamps – we will use the submission datetime to infer the calendar day
SURVEY_DATETIME_COL = "one_click_submitted_datetime"
TARGET_COL = "tired_yesterday"

# ---------------------------------------------------------------------------
# Prepare survey dataframe – extract the calendar date of the *submission*
# ---------------------------------------------------------------------------
# Convert to datetime (the source strings are like "2020-08-21 08:49:08")
survey_df[SURVEY_DATETIME_COL] = pd.to_datetime(survey_df[SURVEY_DATETIME_COL])
# The day the participant answered about *yesterday* is the date portion of the
# submission datetime.
survey_df["survey_date"] = survey_df[SURVEY_DATETIME_COL].dt.date
# The activity record we need corresponds to the previous day.
survey_df["activity_date"] = pd.to_datetime(survey_df["survey_date"]).dt.date - pd.Timedelta(days=1)

# ---------------------------------------------------------------------------
# Filter only the columns we want to keep
# ---------------------------------------------------------------------------
# 1. Sleep‑related columns – they all start with "sleep__" in the activity file.
sleep_cols = [c for c in activity_df.columns if c.startswith("sleep__")]
# 2. Physical‑activity columns – step‑related and active‑fitbit columns.
activity_cols = [c for c in activity_df.columns if c.startswith("steps__") or c.startswith("active_fitbit__")]
# 3. Heart‑rate columns – they start with "heart_rate__".
hr_cols = [c for c in activity_df.columns if c.startswith("heart_rate__")]

# Keep identifier and date as well
selected_activity_cols = [PARTICIPANT_COL, ACTIVITY_DATE_COL] + sleep_cols + activity_cols + hr_cols
activity_df = activity_df[selected_activity_cols]

# ---------------------------------------------------------------------------
# Remove stress / mood columns from the survey side
# ---------------------------------------------------------------------------
# According to the survey dictionary, the following fields are *not* fatigue:
#   - depressed_yesterday, depressed_frequency, pain_yesterday, pain_frequency,
#   - usual_activities_problems, problem_frequency, sleep_yesterday,
#   - day_rating, etc.
# We keep only the fatigue target.
survey_df = survey_df[[PARTICIPANT_COL, "activity_date", TARGET_COL]]

# ---------------------------------------------------------------------------
# Diagnostic reporting
# ---------------------------------------------------------------------------
print(f"Raw activity rows: {len(activity_df)}")
print(f"Raw survey rows: {len(survey_df)}")
print(f"Unique participants in activity: {activity_df[PARTICIPANT_COL].nunique()}")
print(f"Unique participants in survey: {survey_df[PARTICIPANT_COL].nunique()}")

# ---------------------------------------------------------------------------
activity_dups = activity_df.duplicated(subset=[PARTICIPANT_COL, ACTIVITY_DATE_COL], keep=False)
if activity_dups.any():
    print("Warning: duplicate (user_id, date) rows found in activity data – keeping first occurrence.")
    activity_df = activity_df.drop_duplicates(subset=[PARTICIPANT_COL, ACTIVITY_DATE_COL])
survey_dups = survey_df.duplicated(subset=[PARTICIPANT_COL, "activity_date"], keep=False)
if survey_dups.any():
    print("Warning: duplicate (user_id, activity_date) rows found in survey data – keeping first occurrence.")
    survey_df = survey_df.drop_duplicates(subset=[PARTICIPANT_COL, "activity_date"])

# ---------------------------------------------------------------------------
# Merge – inner join on participant and date
# ---------------------------------------------------------------------------
merged = pd.merge(
    survey_df,
    activity_df,
    left_on=[PARTICIPANT_COL, "activity_date"],
    right_on=[PARTICIPANT_COL, ACTIVITY_DATE_COL],
    how="inner",
)

# ---------------------------------------------------------------------------
# Remove records with missing fatigue target (no imputation for target)
# ---------------------------------------------------------------------------
merged = merged.dropna(subset=[TARGET_COL])

# ---------------------------------------------------------------------------
# Participant-level train/test split (80/20)
# ---------------------------------------------------------------------------
unique_participants = merged[PARTICIPANT_COL].unique()
train_participants = pd.Series(unique_participants).sample(frac=0.8, random_state=42).tolist()
train_df = merged[merged[PARTICIPANT_COL].isin(train_participants)].copy()
test_df = merged[~merged[PARTICIPANT_COL].isin(train_participants)].copy()

# ---------------------------------------------------------------------------
# Impute numeric features using median from training data only
# ---------------------------------------------------------------------------
numeric_cols = train_df.select_dtypes(include=["number"]).columns
for col in numeric_cols:
    median = train_df[col].median()
    train_df[col] = train_df[col].fillna(median)
    test_df[col] = test_df[col].fillna(median)

# ---------------------------------------------------------------------------
# Encode ordered fatigue target (consistent across splits)
# ---------------------------------------------------------------------------
order = ["not_at_all", "a_little_bit", "somewhat", "quite_a_bit", "very_much"]
for df in [train_df, test_df]:
    df[TARGET_COL] = pd.Categorical(df[TARGET_COL], categories=order, ordered=True)
    df[f"{TARGET_COL}_code"] = df[TARGET_COL].cat.codes

# ---------------------------------------------------------------------------
# Combine splits for output (retain split label)
# ---------------------------------------------------------------------------
train_df["split"] = "train"
test_df["split"] = "test"
final_df = pd.concat([train_df, test_df], ignore_index=True)

# ---------------------------------------------------------------------------
# Save processed dataset
# ---------------------------------------------------------------------------
output_path = PROCESSED_DIR / "processed_dataset.csv"
final_df.to_csv(output_path, index=False)
print(f"Processed dataset written to {output_path}")
