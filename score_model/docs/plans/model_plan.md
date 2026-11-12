---
title: "Model Plan — Next-Quiz Score and Delayed Retention"
doc_id: "plans/model-plan"
version: "1.0"
status: "draft"
owner: "ML workstream"
created: "2026-11-12"
last_updated: "2026-11-12"
scope: "M6–M11 (CogniSync next-quiz and delayed-retention models)"
data_status: "Blocked — CogniSync quiz records not yet collected"
related:
  - "benchmarks/M5_OULAD_report.md"
  - "benchmarks/evaluation_protocol.md"
  - "plans/personalisation.md"
  - "plans/recommender_plan.md"
---

# Model Plan — Next-Quiz Score and Delayed Retention

This document describes the two student-facing prediction models: the
**next-quiz score model** (M6–M8) and the **delayed-retention model** (M9–M11).
Both are planned, not shipped. Neither can be trained until consented CogniSync
quiz and session records exist.

> **What this model is:** an estimate of how a student is likely to score on an
> upcoming quiz, with an explicit uncertainty state.
>
> **What this model is not:** a grade guarantee, a diagnosis, a measure of
> intelligence, or a fatigue/readiness score. Fatigue and readiness are owned by
> teammates (M17–M18) and are out of scope here.

> **Numbers policy.** The only measured model numbers in this document are the
> OULAD benchmark results, which are explicitly labelled as such. Every
> CogniSync score, retention rate, threshold, and gate result is `[TBD]` until
> consented pilot data exists. No placeholder is filled with a plausible-looking
> estimate.

## 1. Status at a glance

| Component | ID | Status | Training data | Blocker |
|---|---|---|---|---|
| OULAD baselines | M1–M2 | Complete | OULAD | — |
| OULAD Ridge / RF / XGBoost | M3–M5 | Complete | OULAD | — |
| Next-quiz Ridge | M6 | Planned | CogniSync quiz records | No consented data yet |
| Next-quiz Random Forest | M7 | Planned | CogniSync quiz records | No consented data yet |
| Next-quiz XGBoost | M8 | Planned | CogniSync quiz records | No consented data yet |
| Delayed-retention Ridge | M9 | Planned | Delayed-quiz records | No delayed labels yet |
| Delayed-retention Random Forest | M10 | Planned | Delayed-quiz records | No delayed labels yet |
| Delayed-retention XGBoost | M11 | Planned | Delayed-quiz records | No delayed labels yet |
| Personalisation | M12 | Policy drafted | Quiz outcomes | See `personalisation.md` |
| Recommendation ranking | M16 | Policy drafted | Prediction outputs + timetable | See `recommender_plan.md` |

The OULAD benchmark validates the pipeline and model family only. It is not a
performance estimate for CogniSync. The M5 result (XGBoost MAE 9.886, 23.83%
better than last score) is a **reference floor for the engineering process**, not
a promise for student data.

## 2. Data-readiness gate

The next-quiz and retention models are **not shipped** until all of the
following are true:

- [ ] Consented quiz attempts exist, with topic, score, timestamp, and a stable
      pseudonymous student ID.
- [ ] Each attempt links to the study session that preceded it, or is explicitly
      marked as unlinked.
- [ ] At least one repeat quiz per topic exists for a meaningful share of
      students (needed for retention labels).
- [ ] The follow-up window has matured for the evaluation cutoff.
- [ ] The leakage suite passes on the CogniSync feature table.
- [ ] The model beats the score-history baseline on a time-aware split.

Until then, the product ships the **score-history baseline** and an explicit
`insufficient-data` state. A baseline that works is better than a model that
cannot be validated.

### 2.1 Data boundary

| Dataset | Permitted use | Status in this workstream |
|---|---|---|
| OULAD | Offline benchmark only (M1–M5); never deployed as the CogniSync model | Used and reported in `benchmarks/M5_OULAD_report.md` |
| CogniSync quiz / session / delayed-quiz records | Training and evaluation for M6–M12 | Not collected yet |
| Newsela / WikiLarge | Simplification-pair experiments only; edit labels are not factual-entailment labels | Not used for quiz prediction |
| Student Lifestyle dataset | Excluded by PRD §8.2 | Not used |
| SciQ-style Parquet | Excluded by PRD §8.2 | Not used |
| Zenodo / MMASH / PAAWS | Fatigue / readiness workstream (M17–M18, teammates) | Not used here |

## 3. Shared definitions

| Term | Definition |
|---|---|
| Topic | The smallest reusable knowledge unit a quiz is generated from |
| Quiz attempt | One completed quiz, with score, item count, topic, and timestamp |
| Prediction instant (`τ`) | The moment the prediction is made, before the quiz starts |
| Next quiz | The next quiz attempt on a topic after `τ` |
| Delayed quiz | A later quiz on the same topic, separated by a minimum gap |
| Label maturity | The delayed quiz occurred and its outcome is recorded |
| Cold start | A student with no usable prior quiz history |
| Warm start | A student with at least the configured minimum history |

Every feature must be computable from records with timestamp `< τ`. Every label
must come from records with timestamp `≥ τ`.

## 4. Next-quiz score model (M6–M8)

### 4.1 Task

Predict the score of the next quiz attempt on a topic:

```text
target: score ∈ [0, 100]  (or percent correct, normalised to 0–100)
row:    one eligible (student, topic, prediction instant)
```

Eligibility for the history models: at least one prior quiz attempt on the same
topic, or at least one prior attempt overall when using the cross-topic model.
Rows with no history go to the cold-start path, not to training.

### 4.2 Baselines

Every candidate must beat all of these on the same test rows:

| Baseline | Definition | Why it exists |
|---|---|---|
| Last score (same topic) | Most recent prior score on the topic | Strong, simple, hard to beat |
| Topic mean | Mean of the student's prior scores on the topic | Smooths one-off attempts |
| Student overall mean | Mean of all prior scores for the student | Works when topic history is thin |
| Time-of-day heuristic | Student's historical mean score by time-of-day bucket | Product-level floor for scheduling claims |
| Soonest-free-slot heuristic | Recommend the next available window | Product-level floor for recommendations |

### 4.3 Feature groups

| Group | Features | Availability |
|---|---|---|
| Same-topic history | Prior score(s), topic mean, trend, variance, attempt count, days since last attempt, last-attempt difficulty | Available after first attempt |
| Cross-topic history | Overall mean, subject/module mean, recency-weighted mean, number of other topics attempted | Available after first attempt |
| Assessment context | Quiz length, item count, difficulty band, topic weight in upcoming assessment | Needs quiz metadata |
| Session context | Session duration, time of day, day of week, study-session completion | Needs session capture |
| Workload | Upcoming deadlines and assessment load in the next 7 days | Needs timetable |
| Optional recovery | Consented sleep / activity summaries | Only if opted in; owned by M17–M18 |

The model must work with the first four groups. Workload and recovery are
incremental, not required.

### 4.4 Candidate models

| Model | Role | Selection |
|---|---|---|
| Ridge | Interpretable linear baseline | Alpha on validation MAE |
| Random Forest | Non-linear, robust to outliers | Leaf size / depth on validation MAE |
| XGBoost | Strong tabular learner | Depth / rounds on validation MAE |

OULAD showed a meaningful non-linear gain over Ridge on the hardest segment
(TMA R² 0.088 → 0.266). That is a reason to include tree models, not a reason to
assume the same gain on CogniSync.

### 4.5 Split and evaluation

- Forward-chaining by quiz timestamp; student-level holdout.
- No random row split.
- Cold-start and warm-start buckets reported separately.
- Primary metric: MAE. Secondary: RMSE, R², bias, p90 absolute error.
- Student-clustered bootstrap 95% CI.
- Ablation table per `docs/benchmarks/evaluation_protocol.md`.
- Calibration only if the model emits a probability or interval.

### 4.6 Acceptance gate

| Gate | Threshold | Status |
|---|---|---|
| Beats best baseline | ≥ 3% MAE reduction, CI on ΔMAE excludes zero | [TBD] |
| Leakage suite | PASS | [TBD] |
| Cold-start path | Returns a usable baseline with uncertainty | [TBD] |
| Warm-start lift | Positive on students with enough history | [TBD] |
| Reproducibility | Clean run with fixed seed | [TBD] |
| Calibration (if probabilistic) | ECE ≤ 0.05 | [TBD] |

If the gate fails, ship the baseline and re-scope. This is explicitly allowed by
the workstream plan.

### 4.7 Output contract

The model returns a structured prediction, not a bare number:

```yaml
prediction:
  score: 72          # point estimate, 0–100
  interval: [64, 80] # predictive interval, widened when data is thin
  confidence: "medium"  # low | medium | high
  basis: "topic_history" # topic_history | overall_history | cold_start
  n_observations: 6
  model_version: "[TBD]"
  feature_version: "[TBD]"
  reason: "6 prior attempts on this topic; error range widens for short quizzes"
```

Rules:

- Never show a point estimate without a confidence label or interval.
- `confidence = low` when the student is in the cold-start bucket or the topic
  has fewer than the configured minimum observations.
- Never round a prediction up to imply a pass.
- Never compare a student to other students.

### 4.8 Failure modes and fallbacks

| Failure | Detection | Response |
|---|---|---|
| No history | `n_observations = 0` | Cold-start baseline + `insufficient-data` label |
| Thin topic history | `n_observations < N_min` | Topic mean / overall mean, wider interval |
| Quiz metadata missing | Required field null | Fall back to history-only model |
| Schema change | Feature-contract check fails | Disable model, serve baseline |
| Drift | Residual or feature drift alarm | See `personalisation.md` |
| Model service down | Timeout / error | Cached baseline, no silent failure |

## 5. Delayed-retention model (M9–M11)

### 5.1 Task

Predict the score on a delayed quiz on the same topic after a study gap:

```text
target: delayed_score ∈ [0, 100]
row:    one (student, topic, immediate attempt, delayed attempt) tuple
gap:    delayed_timestamp − immediate_timestamp ≥ g_min
```

Proposed `g_min`: 7 days. This is a policy parameter, not a measured value, and
must be fixed before labelling **[TBD]**.

A secondary binary target may be used for student-facing confidence:

```text
retained = 1 if delayed_score ≥ max(pass_threshold, immediate_score − δ)
```

Both the pass threshold and `δ` are **[TBD]** and must be agreed with product.

### 5.2 Baselines

| Baseline | Definition | Why it exists |
|---|---|---|
| Most recent immediate score | Last score on the topic before the gap | Strong persistence baseline |
| Mean of prior delayed scores | Student's history of delayed outcomes | Captures stable retention |
| Exponential decay | `immediate_score × exp(−λ × gap_days)` | Explicit forgetting-curve baseline |
| Topic mean | Mean delayed score for the topic | Population-level floor |

The decay baseline is the key one: a retention model that cannot beat a simple
decay curve has not learned anything useful.

### 5.3 Features

| Group | Features |
|---|---|
| Immediate performance | Immediate score, item count, difficulty, time spent |
| Gap | Days between attempts, number of intervening reviews, review spacing |
| Prior retention | Earlier delayed scores for the topic, retention slope, best/worst gap |
| Topic | Topic difficulty, prerequisite depth, historical retention rate |
| Context | Session context at the immediate attempt, workload during the gap |
| Optional recovery | Consented sleep / activity summaries, if available |

### 5.4 Split and missingness

- Split by student and by the **immediate** attempt timestamp, so the delayed
  outcome never leaks into training.
- Only rows with a matured delayed quiz are evaluation-eligible.
- Report follow-up coverage next to every metric. Students who do not return are
  not a random sample and must not be silently counted as failures.
- Do not impute a missing delayed score as zero.
- Report retention results for at least two gap bands (e.g. 7–14 days and 15–30
  days) **[TBD]**.

### 5.5 Acceptance gate

| Gate | Threshold | Status |
|---|---|---|
| Beats decay baseline | ≥ 3% MAE reduction, CI on ΔMAE excludes zero | [TBD] |
| Beats most-recent-score baseline | ≥ 3% MAE reduction | [TBD] |
| Retention-probability calibration | ECE ≤ 0.05 | [TBD] |
| Follow-up coverage reported | Required for every result | [TBD] |
| Leakage suite | PASS | [TBD] |

### 5.6 Output contract

```yaml
retention_prediction:
  delayed_score: 68
  interval: [55, 81]
  retention_probability: 0.62   # only if the binary target is validated
  gap_days: 14
  confidence: "low"             # low | medium | high
  basis: "decay_baseline"       # model | decay_baseline | insufficient_data
  follow_up_coverage: "[TBD]"
  model_version: "[TBD]"
```

## 6. Ablation and comparison plan

Run the ablation in `docs/benchmarks/evaluation_protocol.md` for both models.
Minimum comparisons:

| Comparison | Question |
|---|---|
| History only vs history + cross-topic | Does cross-topic history add signal? |
| + assessment context | Does quiz difficulty/length help? |
| + session context | Does study-session context help? |
| + workload | Do deadlines improve prediction? |
| + optional recovery | Does consented recovery data add value beyond history? |
| Ridge vs RF vs XGBoost | Is the non-linear gain real on CogniSync? |
| Global vs calibrated | Does personalisation help warm-start students? |

Report every row with `[TBD]` until measured. Do not delete losing rows from the
table; negative ablations are results.

## 7. Data requirements

| Field | Type | Required | Status |
|---|---|---|---|
| `quiz_attempt_id` | string | Yes | Not collected |
| `student_id` (pseudonymous) | string | Yes | Not collected |
| `topic_id` | string | Yes | Not collected |
| `attempt_timestamp` | ISO-8601 | Yes | Not collected |
| `score` | float 0–100 | Yes | Not collected |
| `max_score` / item count | int | Yes | Not collected |
| `session_id` | string | Preferred | Not collected |
| `source_material_id` | string | Preferred | Not collected |
| `difficulty_band` | enum | Optional | Not collected |
| `quiz_generated_by` | enum | Optional | Not collected |
| `delayed_of_attempt_id` | string | Retention only | Not collected |

Data-quality rules:

- Scores must be attached to the correct session and topic, never to "latest
  session".
- Timestamps must be server-side, not client-editable.
- Deleted or reset attempts are logged, not silently removed.
- Every feature snapshot records the schema and feature version.

## 8. Personalisation hook

The next-quiz model is the global model. Per-student calibration is layered on
top only after enough observations. The full policy — EWMA residual correction,
minimum observation count, shrinkage, caps, and drift response — is in
`docs/plans/personalisation.md`.

Summary:

```text
global prediction
  → per-student bias correction (after N_min observations)
  → personal refit (only for high-history students)
  → fallback to global when correction is unstable
```

## 9. Shipping sequence

| Step | Deliverable | Exit condition |
|---|---|---|
| 1 | Score-history baseline | Works with zero personal data; explicit `insufficient-data` state |
| 2 | Global next-quiz model | Beats baseline on time-aware split; leakage pass |
| 3 | Calibrated predictions | Intervals and confidence labels match observed coverage |
| 4 | Delayed-retention model | Beats decay baseline with matured labels |
| 5 | Personalised correction | Improves warm-start students without hurting cold start |
| 6 | Recommender integration | Ranking beats heuristics; fallback works |

No step is skipped because a later step looks more exciting.

## 10. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| CogniSync data never reaches usable volume | Models cannot ship | Ship baseline; keep collection friction low |
| Topic history is too sparse | Cold start dominates | Topic mean + overall mean + explicit uncertainty |
| Students disengage before delayed quiz | Retention labels missing | Report coverage; do not impute failure |
| OULAD ≠ CogniSync | False confidence | Benchmark only; never claim transfer |
| Feature drift | Silent accuracy loss | Version features; monitor residuals; recalibrate |
| Overclaiming | Trust and compliance risk | No grade guarantees; no causal language |
| Quiz quality varies | Label noise | Track item count/difficulty; segment evaluation |
| Leakage through session linkage | Inflated results | Point-in-time audit + negative controls |

## 11. Open questions

| Question | Owner | Status |
|---|---|---|
| What is the minimum topic history for a usable prediction? | ML | [TBD] |
| What gap defines "delayed" for CogniSync? | ML + product | [TBD] |
| Is the retention target a score or a binary outcome? | ML + product | [TBD] |
| How should unlinked quiz attempts be handled? | ML + backend | [TBD] |
| What is the user-facing wording for "low confidence"? | Product | [TBD] |
| Which optional recovery features can be consumed without crossing the M17/M18 boundary? | ML + teammates | [TBD] |
| What is the retraining cadence after launch? | ML | [TBD] |

## 12. Plan traceability

| `ML_WORKSTREAM_PLAN.md` step | Where it is covered |
|---|---|
| Step 1 — OULAD audit and prep | `benchmarks/M5_OULAD_report.md` (protocol, data summary, leakage tests) |
| Steps 2–3 — OULAD baselines and trainable benchmarks (M1–M5) | `benchmarks/M5_OULAD_report.md` |
| Step 4 — next-quiz score model (M6–M8) | Sections 4 and 6 of this document |
| Step 5 — delayed-retention model (M9–M11) | Sections 5 and 6 of this document |
| Step 6 — personalisation (M12) | `plans/personalisation.md` |
| Step 7 — recommendation ranking (M14–M16) | `plans/recommender_plan.md` |
| Step 8 — evaluation protocol | `benchmarks/evaluation_protocol.md` |
| Go / no-go gates and data readiness | Section 2 and Section 4.6 above; `benchmarks/evaluation_protocol.md` §5.3 |
| Risks | Section 10 above |
