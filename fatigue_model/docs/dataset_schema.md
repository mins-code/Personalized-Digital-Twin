# Dataset Schema

## Source Files
- `data/raw/day_activity_features.csv` – Daily aggregated wearable sensor features per participant.
- `data/raw/daily_surveys_one_click_responses.csv` – One‑click fatigue survey responses.
- `data/raw/activity_feature_data_dictionary.csv` – Descriptions of every feature column in the activity file.
- `data/raw/daily_survey_data_dictionary.csv` – Definitions of survey questions and answer encodings.

## Key Columns Identified
| Role | Column | Description |
|------|--------|-------------|
| Participant Identifier | `user_id` | Unique anonymised ID for each participant (present in both activity and survey files). |
| Activity Date | `date` | Calendar date (YYYY‑MM‑DD) for which the wearable summary was computed. |
| Survey Submission Timestamp | `one_click_submitted_datetime` | Timestamp when the participant submitted the one‑click survey. |
| Derived Survey Date | `survey_date` (derived) | Date part of `one_click_submitted_datetime`. |
| Target (Fatigue) | `tired_yesterday` | Self‑reported fatigue level for **the day before** the survey (ordered categories). |

## Feature Groups (kept)
### Sleep‑related (prefix `sleep__`)
- `sleep__asleep__mean`, `sleep__asleep__sum`, `sleep__awake__mean`, `sleep__awake__sum`, `sleep__awake_regions__countDistinct`, `sleep__main_efficiency`, `sleep__main_in_bed_minutes`, `sleep__main_start_time`, `sleep__nap_count`, `sleep__really_awake__mean`, `sleep__really_awake__sum`, `sleep__really_awake_regions__countDistinct`, `sleep__sleeping__sum`, `sleep__total_asleep_minutes`, `sleep__total_in_bed_minutes`, … (all columns whose name starts with `sleep__`).

### Physical‑activity (prefix `steps__` or `active_fitbit__`)
- `steps__count`, `steps__dec_time__max`, `steps__dec_time__min`, `steps__light_activity__sum`, `steps__mvpa__sum`, `steps__not_moving__sum`, `steps__rolling_6_sum__max`, `steps__sedentary__sum`, `steps__streaks__countDistinct`, `steps__sum`, `steps__midday_steps_dec_time`, `steps__first_step_dec_time`, `steps__last_step_dec_time`, `steps__max_rolling_1` … (all columns beginning with `steps__`).
- `active_fitbit__awake__sum`, `active_fitbit__sum` – minutes the Fitbit was worn while awake / overall.

### Heart‑rate (prefix `heart_rate__`)
- `heart_rate__asleep__max`, `heart_rate__asleep__mean`, `heart_rate__asleep__stddev`, `heart_rate__awake__max`, `heart_rate__awake__mean`, `heart_rate__awake__stddev`, `heart_rate__mean`, `heart_rate__max`, `heart_rate__min`, `heart_rate__median`, `heart_rate__resting_heart_rate`, `heart_rate__stddev`, `heart_rate__perc_25th`, `heart_rate__perc_50th`, `heart_rate__perc_75th`, `heart_rate__perc_95th`, `heart_rate__autocorr10min`, `heart_rate__autocorr1min`, `heart_rate__autocorr2min`, `heart_rate__autocorr3min`, `heart_rate__autocorr60min`, `heart_rate__count`, `heart_rate__high_150_perc_resting_frac`, `heart_rate__high_200_perc_resting_frac`, `heart_rate__peaks`, `heart_rate__peaks_gt_125_perc_median`, `heart_rate__peaks_gt_150_perc_median`, `heart_rate__peaks_gt_200_perc_median`, `heart_rate__quant_95th_to_resting_ratio`, … (all columns starting with `heart_rate__`).

## Excluded Fields
All columns **not** belonging to the three groups above and any survey columns other than `tired_yesterday` are omitted, e.g.:
- Stress / mood: `depressed_yesterday`, `depressed_frequency`, `pain_yesterday`, `pain_frequency`, `usual_activities_problems`, `problem_frequency`, `sleep_yesterday`, `day_rating`, etc.
- Any event‑based columns such as `bmi`, `calories_burned`, `run_meters`, `weight_kg` that are not part of the defined feature groups.

## Join Logic
1. Convert `one_click_submitted_datetime` to a date → `survey_date`.
2. The fatigue question asks about **yesterday**, therefore the activity record that matches the **previous calendar day** (`activity_date = survey_date - 1 day`) is linked.
3. Join on:
   - `user_id`
   - `activity_date` (derived) ↔ `date` in `day_activity_features.csv`
   Using an inner join (records without a matching activity day are dropped).

## Pre‑processing Steps (implemented in `src/preprocessing.py`)
- Load the four CSV files.
- Derive `survey_date` and `activity_date` as described.
- Select only the verified feature columns (sleep, activity, heart‑rate) plus identifiers.
- Keep only the fatigue target column `tired_yesterday`.
- Perform an inner merge on `user_id` and `activity_date`.
- Missing numeric values → median imputation; missing target values → most‑frequent category.
- Encode `tired_yesterday` as an ordered categorical with the order
  `not_at_all < a_little_bit < quite_a_bit < somewhat < very_much` (derived from the survey dictionary).
- Add a numeric code column `tired_yesterday_code` for downstream modeling.
- Write the final tidy table to `data/processed/processed_dataset.csv`.
- Participant IDs are retained in the output but can be used later for participant‑level train/test splitting.

## Uncertainties / Notes
- The activity file contains additional event‑based columns (e.g., `bmi`, `calories_burned`) that are not described in the dictionary as sleep / activity / HR. They are excluded by design.
- If any participant lacks an activity record for the required previous day, that survey entry is dropped (inner join). This behaviour is documented but may be revisited if more sophisticated alignment is needed.

