---
title: "Evaluation Protocol — Metrics, Splits, and Ablations"
doc_id: "benchmarks/evaluation-protocol"
version: "1.0"
status: "draft"
owner: "ML workstream"
created: "2026-11-12"
last_updated: "2026-11-12"
applies_to: "M1–M16 (OULAD benchmark and future CogniSync models)"
related:
  - "benchmarks/M5_OULAD_report.md"
  - "plans/model_plan.md"
  - "plans/personalisation.md"
  - "plans/recommender_plan.md"
---

# Evaluation Protocol — Metrics, Splits, and Ablations

This protocol applies to every model in the ML workstream. It exists so that
results are comparable across models, cohorts, and time, and so that no model is
declared better because of a leak or an easy split.

> **Rule zero:** if a result cannot be reproduced from a clean checkout with a
> fixed seed, it is not a result.

> **Measured vs planned.** The only measured model results in this workstream
> are the OULAD benchmark numbers recorded in `benchmarks/M5_OULAD_report.md`
> and `benchmarks/oulad_results.json`. Every CogniSync metric, threshold, and
> gate result in this protocol and the model documents is `[TBD]` until
> consented pilot data exists. Do not replace a `[TBD]` with an estimate.

## 1. Scope

| In scope | Out of scope |
|---|---|
| OULAD score-prediction benchmark (M1–M5) | Fatigue / readiness models (M17–M18, teammates) |
| CogniSync next-quiz score models (M6–M8) | Mood, stress, or medical inference |
| CogniSync delayed-retention models (M9–M11) | Claims of causal grade improvement |
| Per-student calibration (M12) | Claims that OULAD performance transfers to CogniSync |
| Recommendation ranking evaluation (M16) | LLM / summarisation quality evaluation |

## 2. Golden rules

1. **No random row splits.** Split by student and by time. A random row split
   leaks a student's other attempts, and often the future, into training.
2. **Point-in-time features only.** Every feature must be computable strictly
   before the prediction instant. Write the prediction instant into the row and
   test it.
3. **Baselines on every table.** History mean and last score are the floor for
   score prediction. Time-of-day and soonest-free-slot heuristics are the floor
   for recommendations.
4. **Touch the test set once.** Hyper-parameters are selected on validation.
   Test-driven tuning invalidates the test set.
5. **Report uncertainty.** Point estimates alone are not enough; use
   student-clustered confidence intervals.
6. **Report missingness.** Students who do not return are not a random sample.
7. **No causal or grade-guarantee language.** Report prediction error, not
   learning improvement.
8. **Mark unmeasured values `[TBD]`.** Never fill a table with plausible-looking
   numbers.

## 3. Splits

### 3.1 OULAD benchmark

| Split | Presentations | Role |
|---|---|---|
| Train | 2013B, 2013J | Fit models and imputers |
| Validation | 2014B | Select hyper-parameters |
| Test | 2014J | Final one-shot evaluation |

Requirements:

- Presentations are ordered by calendar time.
- Students are pairwise disjoint across train, validation, and test. A student
  seen in an earlier split is removed from every later split.
- Rows without at least one visible prior attempt are excluded from score-history
  benchmarks.
- Test rows are never used for imputation, scaling, feature selection, or early
  stopping.

### 3.2 CogniSync models (future data)

CogniSync records arrive as a stream, so evaluation uses time-aware holdouts:

| Scheme | Definition | Use |
|---|---|---|
| Forward-chaining | Train on weeks 1..k, validate on k+1, test on k+2; roll forward | Primary evaluation |
| Student holdout | Entire students held out, not individual rows | Generalisation to new students |
| Cold-start bucket | Students with 0 prior attempts | Baseline / fallback evaluation |
| Warm-start bucket | Students with ≥ N prior attempts | Personalisation evaluation |

Rules:

- The split boundary is a timestamp, not a row index.
- A student's later attempts never appear in an earlier training window.
- Delayed-retention labels must have matured before the evaluation cutoff.
  Otherwise the label is right-censored and must be reported as missing.
- Report the number of students and rows in every bucket, not just the total.

### 3.3 Recommended minimum cohort sizes

These are planning thresholds, not measured results:

| Bucket | Minimum rows | Minimum students | Status |
|---|---:|---:|---|
| Global next-quiz model | [TBD] | [TBD] | To be fixed after pilot |
| Per-student calibration | 5–10 observations per student | — | Proposed range from the plan |
| Delayed-retention model | [TBD] | [TBD] | Depends on follow-up window |
| Recommendation offline replay | [TBD] | [TBD] | Needs logged candidate windows |

## 4. Metrics

### 4.1 Score prediction (regression)

| Metric | Formula | Role |
|---|---|---|
| MAE | `mean(abs(ŷ − y))` | Primary metric; interpretable in marks |
| RMSE | `sqrt(mean((ŷ − y)²))` | Secondary; penalises large errors |
| R² | `1 − SS_res / SS_tot` | Variance explained; report only when meaningful |
| Bias | `mean(ŷ − y)` | Detects systematic over/under-prediction |
| p90 absolute error | 90th percentile of `abs(ŷ − y)` | Tail behaviour |
| Coverage | Share of rows with a usable prediction | Data-readiness signal |

MAE is the decision metric because it is in the same unit as the score and is
robust to the long error tails seen in OULAD. RMSE and R² are reported for
comparability, not for model selection on their own.

### 4.2 Calibration (probability or interval outputs)

Use these when the model emits a probability (e.g. "will retain", "score below
40") or a predictive interval.

| Metric | Definition | Target |
|---|---|---|
| Expected Calibration Error (ECE) | Weighted mean gap between predicted probability and observed frequency across bins | [TBD]; proposed ≤ 0.05 |
| Brier score | `mean((p − y)²)` for binary outcomes | Lower is better; compare to base rate |
| Reliability slope | Slope of observed frequency on predicted probability | Close to 1.0 |
| Interval coverage | Share of outcomes inside the stated interval | Close to nominal (e.g. 90%) |
| Interval width | Mean width of the predictive interval | Narrower is better at fixed coverage |

A model that is accurate on average but overconfident is not shippable for
student-facing displays.

### 4.3 Recommendation ranking

| Metric | Definition | Role |
|---|---|---|
| NDCG@k | Normalised discounted cumulative gain of the ranked windows | Primary offline ranking metric |
| Recall@k | Share of relevant windows in the top k | Coverage of useful options |
| MRR | Mean reciprocal rank of the first relevant window | How early the best option appears |
| Act-on rate | Share of recommendations that lead to a session start within 24 h | Primary online metric |
| Completion rate | Share of started recommended sessions that are completed | Quality guardrail |
| Candidate coverage | Share of available windows that can be scored | Fallback / cold-start signal |
| Diversity | Spread of recommended topics and times | Anti-repetition guardrail |

Relevance labels must be defined before evaluation. Proposed definitions:
"student accepted and completed the session", or "session led to a quiz attempt
on the targeted topic". Both are **[TBD]** until pilot data exists.

### 4.4 Delayed retention

| Metric | Definition | Role |
|---|---|---|
| MAE on delayed score | Primary accuracy metric | Compare against decay baseline |
| RMSE | Secondary accuracy | Tail behaviour |
| Retention-probability Brier | Calibration of "retained / not retained" | Student-facing confidence |
| Follow-up coverage | Share of eligible students with a matured delayed quiz | Missingness disclosure |
| Time-to-next-review error | Error in predicted days to next review | Scheduling quality |

Missing delayed quizzes are **not** automatically failures. Report them as
missing and show follow-up coverage next to every retention metric.

## 5. Uncertainty and statistical comparison

### 5.1 Student-clustered bootstrap

Attempts from the same student are correlated. Resample **students**, not rows:

1. Aggregate absolute errors and squared errors per student.
2. Draw `B` bootstrap samples of students with replacement.
3. Recompute MAE and RMSE per draw.
4. Report the 2.5th and 97.5th percentiles.

Defaults:

| Setting | Value |
|---|---|
| Draws | 1,000 |
| Seed | 42 |
| Cluster unit | `id_student` |
| Reported interval | Percentile 95% |

The final M5 run used 1,000 draws. Earlier development runs with fewer draws
(for example, a 200-draw smoke test) are not reportable results and must not be
mixed with the final run.

### 5.2 Model comparison

Report the paired difference, not just whether intervals overlap:

```text
ΔMAE = MAE(baseline) − MAE(candidate)
```

Compute the bootstrap distribution of `ΔMAE` by resampling students and
reporting the 95% interval. A candidate is "meaningfully better" only if the
interval excludes zero **and** the relative improvement clears the pre-registered
gate.

### 5.3 Pre-registered gates

| Model family | Gate | Status |
|---|---|---|
| OULAD benchmark | Beat last score by ≥ 3% MAE | PASS (23.83%, see M5 report) |
| Next-quiz score | Beat best baseline by ≥ 3% MAE, CI excludes zero | [TBD] |
| Delayed retention | Beat decay baseline by ≥ 3% MAE, CI excludes zero | [TBD] |
| Personalisation | Beat global model on warm-start students without hurting cold-start | [TBD] |
| Recommender | Beat time-of-day and soonest-free-slot heuristics on act-on rate | [TBD] |

If a gate fails, ship the simpler baseline. This is a product decision rule, not
a failure of the workstream.

## 6. Leakage checks

Run these for every feature rebuild:

| Check | What it proves | Failure means |
|---|---|---|
| Point-in-time audit | No ordering violations; target and `final_result` absent | Feature builder is using future data |
| Independent spot recomputation | Cumulative-sum code matches a naive per-row filter | Grouping, tie, or sort bug |
| Future-row invariance | Deleting future rows leaves past features bit-identical | Cohort or full-history statistics leaked in |
| Student-disjoint splits | No student appears in two splits | Identity leakage |
| Negative controls | Deliberately leaky probes are caught | The detector is too weak |
| Schema snapshot | Feature names and dtypes match the training contract | Silent upstream change |

Negative controls are mandatory. A leakage suite that never fails is not
evidence of correctness; it must catch a target-score probe and a future-mean
probe.

## 7. Ablation protocol

### 7.1 Purpose

An ablation answers one question: **what does each feature group add?** It is not
a hyper-parameter search. Run it once per model family, with the same split,
seed, and preprocessing contract.

### 7.2 Feature groups

| Code | Group | Examples | Owner |
|---|---|---|---|
| H | Same-topic history | Prior score, topic mean, trend, variance, attempt count, days since last attempt | ML |
| X | Cross-topic history | Overall student mean, subject mean, recency-weighted mean, other-topic attempts | ML |
| A | Assessment metadata | Assessment type, weight, position in module, days to deadline | ML |
| E | Enrolment / demographics | Registration timing, prior attempts, credits, education band, region, disability | ML |
| C | Context | Session duration, time of day, day of week, workload, commute window | ML |
| R | Optional recovery | Consented sleep / activity features | Teammates (M17–M18); consume only if exposed and consented |

`R` is never required. Models must work with `H + X + A + E + C` alone.

### 7.3 Ablation template

Copy this table into the model report and fill it in. Use `[TBD]` until measured.

| Run | Feature groups | Model | MAE | ΔMAE vs baseline | 95% CI on ΔMAE | RMSE | R² | Calibration (ECE) | n rows | n students |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|
| B0 | None (last score, same topic) | Baseline | [TBD] | — | — | [TBD] | [TBD] | — | [TBD] | [TBD] |
| B1 | None (topic mean) | Baseline | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | — | [TBD] | [TBD] |
| A0 | H | Ridge | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| A1 | H + X | Ridge | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| A2 | H + X + A | Ridge | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| A3 | H + X + A + E | Ridge | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| A4 | H + X + A + E + C | Ridge | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| A5 | A4 + R (if available) | Ridge | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| A6 | H + X + A + E + C | Random Forest | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| A7 | H + X + A + E + C | XGBoost | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |

Rules for filling the template:

- Keep the split and seed fixed across rows.
- Add groups cumulatively; do not swap groups between rows.
- Report `ΔMAE` against the **same** baseline for every row.
- Report the CI on the difference, not two separate CIs.
- Record the feature version (`features_vX.Y`) next to the table.
- Run the cold-start bucket separately; do not average it with warm-start.

### 7.4 Ablation log entry

Every ablation run records:

```yaml
run_id: "[TBD]"
date: "[TBD]"
model_family: "ridge | random_forest | xgboost"
feature_version: "[TBD]"
feature_groups: "[TBD]"
train_window: "[TBD]"
val_window: "[TBD]"
test_window: "[TBD]"
seed: 42
n_rows_train: "[TBD]"
n_rows_test: "[TBD]"
n_students_test: "[TBD]"
metrics:
  mae: "[TBD]"
  rmse: "[TBD]"
  r2: "[TBD]"
  bias: "[TBD]"
  p90_abs_error: "[TBD]"
  calibration_ece: "[TBD]"
baseline: "[TBD]"
delta_mae: "[TBD]"
delta_mae_ci95: "[TBD]"
leakage_suite: "PASS | FAIL"
notes: "[TBD]"
```

## 8. Reporting checklist

Every model report must include:

- [ ] Model ID, version, owner, date.
- [ ] Prediction target and prediction instant.
- [ ] Rows, students, and target mean/sd for train, validation, and test.
- [ ] Split definition, including how many rows were dropped to enforce it.
- [ ] Feature groups and feature version.
- [ ] Leakage-suite result and negative-control results.
- [ ] Baseline values on the same test rows.
- [ ] MAE, RMSE, R², bias, p90 absolute error.
- [ ] Student-clustered 95% CIs with the number of draws and clusters.
- [ ] Error by assessment type and by course/module where sample size allows.
- [ ] Calibration metrics if probabilities or intervals are emitted.
- [ ] Ablation table.
- [ ] Cold-start and missing-data behaviour.
- [ ] Gate decision: GO / NO-GO / more data needed.
- [ ] Explicit `[TBD]` list for anything not measured.
- [ ] Reproduction command and package versions.

## 9. Anti-patterns

| Anti-pattern | Why it is invalid |
|---|---|
| Random `train_test_split` on rows | Same student and adjacent attempts appear on both sides |
| Scaling or imputing before the split | Test statistics leak into training |
| Using `final_result` as a feature | End-of-module outcome, unavailable at prediction time |
| Selecting features on the test set | Test set is no longer held out |
| Reporting one seed only after tuning on it | Result is selected for luck |
| Row-level bootstrap | Understates uncertainty because attempts are correlated |
| Treating missing delayed quizzes as failures | Missingness is informative and usually not random |
| Reporting R² on a narrow or shifted cohort without context | R² is relative to that cohort's variance |
| Claiming OULAD results transfer to CogniSync | Different task, population, and label process |

## 10. Versioning and reproducibility

| Artifact | Versioning rule |
|---|---|
| Feature table | `features_vMAJOR.MINOR`; bump MAJOR on any semantic change |
| Model | `model_<name>_vMAJOR.MINOR`; bump on retrain or parameter change |
| Split definition | Immutable per evaluation; new split = new report |
| Results JSON | Committed with the report and the code revision |
| Seed | Fixed and recorded |
| Dependencies | Pin versions in the report |

A result is reproducible when a clean checkout plus the recorded command, seed,
and dependency versions regenerates the reported table within rounding.

## 11. Open items

| Item | Status | Owner |
|---|---|---|
| Finalise CI draw count (200 vs 1,000) for all reports | [TBD] | ML |
| Define CogniSync relevance label for recommender evaluation | [TBD] | ML + product |
| Define minimum cohort sizes for each model | [TBD] | ML |
| Agree calibration target (ECE threshold) | [TBD] | ML + product |
| Add paired-bootstrap comparison utility | [TBD] | ML |
| Automate ablation table generation | [TBD] | ML |
| Freeze feature schema for the pilot | [TBD] | ML + backend |
