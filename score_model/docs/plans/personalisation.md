---
title: "Personalisation — Calibration and Drift Policy"
doc_id: "plans/personalisation"
version: "1.0"
status: "draft"
owner: "ML workstream"
created: "2026-11-12"
last_updated: "2026-11-12"
scope: "M12 — per-student calibration"
related:
  - "plans/model_plan.md"
  - "benchmarks/evaluation_protocol.md"
  - "plans/recommender_plan.md"
---

# Personalisation — Calibration and Drift Policy

This document defines how a global prediction becomes a student-specific
prediction, when personalisation is allowed, and how drift is detected and
handled. It is a policy document: all thresholds are proposed defaults until
they are validated on CogniSync data.

> **Principle:** personalise late, shrink hard, and fall back early. A global
> model that is honest about uncertainty is better than a personalised model
> that is confidently wrong.

> **Numbers policy.** `N_min`, `N_refit`, EWMA `alpha`, shrinkage `k`, correction
> caps, drift thresholds, and every acceptance-gate result are proposed defaults
> or `[TBD]` until validated on CogniSync pilot data. They are not measured
> results, and no synthetic calibration curve is presented as evidence.

## 1. Scope and non-goals

| In scope | Out of scope |
|---|---|
| Per-student bias correction | Diagnosing ability, disability, or mental health |
| Shrinkage toward the global model | Ranking students against each other |
| Cold-start and warm-start handling | Fatigue / readiness modelling (M17–M18) |
| Calibration curves and drift monitoring | Causal claims about learning gains |
| Reverting to global on instability | Grade guarantees |

## 2. Definitions

| Term | Definition |
|---|---|
| Global model | Shared model trained across students |
| Residual | `actual − predicted` for one observation |
| Bias correction | Per-student offset added to the global prediction |
| EWMA | Exponentially weighted moving average of residuals |
| Shrinkage | Weighting a student's own estimate by how much data supports it |
| Cold start | Student below the minimum observation count |
| Warm start | Student at or above the minimum observation count |
| Calibration | Agreement between predicted uncertainty and observed outcomes |
| Drift | Change in the input distribution or the residual distribution over time |

## 3. Calibration ladder

Personalisation is applied in stages. A stage is only enabled when the evidence
supports it.

| Level | Name | Method | Data requirement | Status |
|---|---|---|---|---|
| L0 | Global | Shared model, no personal adjustment | Any | Baseline |
| L1 | Bias-corrected | Global prediction + EWMA residual offset | ≥ `N_min` observations | Planned |
| L2 | Personal refit | Student-specific model shrunk toward global | ≥ `N_refit` observations | Planned |
| L3 | Segment model | Cohort-level model (e.g. by topic family) | Segment-level data | Not planned |

Default thresholds (proposed, not measured):

| Parameter | Proposed default | Range to test |
|---|---:|---|
| `N_min` (enable bias correction) | 8 observations | 5–10 |
| `N_refit` (enable personal refit) | 30 observations | 20–50 |
| EWMA `alpha` | 0.20 | 0.10–0.30 |
| Shrinkage constant `k` | 10 observations | 5–20 |
| Maximum absolute correction | ±10 score points | ±5–±15 |
| Minimum observations per topic for topic-level correction | 3 | 2–5 |

All values are **[TBD]** until tuned on a chronological, student-held-out
validation set.

## 4. Method

### 4.1 L1 — EWMA bias correction

For student `s` at observation `t`:

```text
residual_t   = actual_t − global_prediction_t
ewma_t       = alpha × residual_t + (1 − alpha) × ewma_{t−1}
```

Sign convention: the workstream plan writes the residual as `predicted −
actual`; this document uses the equivalent `actual − predicted` so that the
correction can be added to the global prediction. The two forms differ only in
sign.

Prediction:

```text
personal_prediction = clip(global_prediction + shrink × ewma_t, 0, 100)
```

Where:

```text
shrink = n_s / (n_s + k)
n_s    = number of observations for the student
k      = shrinkage constant
```

Properties:

- New students get `shrink ≈ 0`, so the global model dominates.
- Students with many observations get a correction close to their own residual.
- The correction cannot move a prediction outside the valid score range.
- The correction is capped at ±10 points to prevent a single bad streak from
  dominating.

### 4.2 L2 — Personal refit

Only for students with `n_s ≥ N_refit`:

```text
personal_model = Ridge(alpha = alpha_personal)
                 fit on the student's observations
                 with a prior centred on the global model
```

The global model's coefficients are used as the prior mean, and `alpha_personal`
controls how far the personal model can move away. The exact parameterisation is
**[TBD]**; the policy requirement is that a personal refit can never be more
extreme than the shrunk L1 correction without out-of-sample evidence.

### 4.3 What is *not* personalised

- The target definition.
- The feature set.
- The uncertainty floor.
- The pass/fail threshold.
- The recommendation hard constraints.

Only the expected score and its interval are adjusted. The model must not learn
a different notion of "good" for different students.

## 5. Student-facing confidence

Every prediction carries a confidence label derived from data volume and
residual stability.

| Label | Conditions (proposed) | Display |
|---|---|---|
| `insufficient_data` | `n_s < N_min` | "Not enough history yet — showing a general estimate" |
| `low` | `N_min ≤ n_s < 2 × N_min` or high residual variance | Wide interval; no strong claim |
| `medium` | `2 × N_min ≤ n_s < N_refit` and stable residuals | Normal interval |
| `high` | `n_s ≥ N_refit` and stable residuals and recent calibration check passed | Narrowest interval |

Confidence must never be raised just because the point estimate looks plausible.
It is a function of evidence, not of the predicted score.

## 6. Evaluation protocol

### 6.1 Comparisons

| Comparison | Question | Primary metric |
|---|---|---|
| L0 vs L1 | Does bias correction help? | MAE on warm-start students |
| L1 vs L2 | Does personal refit add value? | MAE on high-history students |
| L0 vs L1 on cold start | Does personalisation hurt new students? | MAE on cold-start bucket |
| Per-student lift distribution | Is the average hiding harm? | Share of students improved / unchanged / worse |
| Calibration curve | Are intervals honest? | Coverage vs nominal, ECE |

### 6.2 Rules

- Chronological evaluation per student; never train on a student's future
  attempts.
- Report cold-start and warm-start buckets separately.
- Report the **distribution** of per-student MAE change, not only the mean. A
  positive average with a long negative tail is not a win.
- Report a paired bootstrap CI on the per-student difference.
- Require the calibration curve to be plotted before shipping any confidence
  label.
- Do not compare students to each other in the evaluation output.

### 6.3 Acceptance gate

| Gate | Threshold | Status |
|---|---|---|
| Warm-start MAE improves | ≥ 3% relative, CI excludes zero | [TBD] |
| Cold-start MAE does not degrade | ≤ 1% relative degradation | [TBD] |
| Students made worse | ≤ 10% of warm-start students by more than 2 points | [TBD] |
| Interval coverage | Within ±5 percentage points of nominal | [TBD] |
| Calibration ECE | ≤ 0.05 | [TBD] |
| Rollback tested | Global fallback restores baseline metrics | [TBD] |

If any gate fails, L1/L2 stays off and the product continues with L0 plus the
explicit `insufficient_data` state.

## 7. Drift policy

Drift is expected: students change courses, quiz difficulty changes, and
populations shift by term. The policy is to detect early, shrink first, and
retrain only with evidence.

### 7.1 Signals and thresholds

| Signal | Definition | Warning | Critical | Action |
|---|---|---:|---:|---|
| Residual mean shift | EWMA of `actual − predicted` | \|shift\| > 3 points | \|shift\| > 5 points for 3 batches | Recalibrate bias |
| MAE degradation | Rolling MAE vs reference window | +10% relative | +20% relative for 2 windows | Investigate / retrain |
| Feature drift (PSI) | Population stability index on high-importance features | PSI > 0.10 | PSI > 0.20 | Review feature pipeline |
| Missingness | Share of required features missing | > 10% | > 20% | Fall back to baseline |
| Confidence miscalibration | Observed coverage vs stated interval | ±5 pp | ±10 pp | Recalibrate intervals |
| Label delay | Share of labels matured by evaluation cutoff | < 80% | < 60% | Delay evaluation; report coverage |
| Schema drift | Feature contract mismatch | Any | Any | Disable model, serve baseline |
| Cohort shift | New topic/module share | > 20% of traffic | > 40% of traffic | Segment evaluation |

Thresholds are proposed defaults and must be tuned per signal **[TBD]**.

### 7.2 Response ladder

Use the least invasive action that restores calibration:

| Step | Action | Trigger | Reversible |
|---|---|---|---|
| 1 | Monitor | Warning signal | — |
| 2 | Recalibrate bias / intervals | Residual shift or miscalibration | Yes |
| 3 | Shrink personalisation | Per-student instability | Yes |
| 4 | Fall back to global model | Critical drift or missing features | Yes |
| 5 | Fall back to score-history baseline | Model unavailable or unvalidated | Yes |
| 6 | Retrain on a newer window | Sustained MAE degradation | Via versioned release |
| 7 | Roll back to previous model version | Retrain does not recover | Yes |

Every action is logged with the trigger, the metric value, the model version,
and the feature version.

### 7.3 Monitoring cadence

| Check | Cadence | Owner |
|---|---|---|
| Per-student bias update | Every new observation | Online job |
| Residual and MAE dashboard | Daily | ML |
| Calibration curve | Weekly | ML |
| Feature drift (PSI) | Weekly | ML |
| Full re-evaluation on a holdout | Monthly or per release | ML |
| Retraining decision | Monthly review | ML + product |

Cadence is **[TBD]** until traffic volume is known. Low-traffic periods should
widen intervals rather than pretend precision.

## 8. Guardrails

- **Cap the correction.** No single student's offset may exceed ±10 points
  without a fresh validation.
- **Never correct a cold-start student.** `n_s < N_min` means L0 only.
- **No cross-student pooling of personal residuals.** Student records stay
  isolated; aggregate statistics are computed from consented, de-identified
  data only.
- **No mood, stress, or medical inference.** These fields are absent from the
  schema and the feature set.
- **No hidden personalisation.** The UI states when a prediction is
  personalised and when it is a general estimate.
- **No irreversible action.** A student can reset personalisation; the global
  model remains available.
- **No grade guarantee.** Calibration improves the estimate, not the outcome.

## 9. Logging and audit

For each prediction, log:

```yaml
prediction_id: "[TBD]"
student_id_hash: "[TBD]"      # pseudonymous, not reversible
model_version: "[TBD]"
feature_version: "[TBD]"
calibration_level: "L0 | L1 | L2"
n_observations: "[TBD]"
global_prediction: "[TBD]"
correction: "[TBD]"
final_prediction: "[TBD]"
interval: "[TBD]"
confidence: "[TBD]"
fallback_reason: "[TBD]"
timestamp: "[TBD]"
```

Retention of logs follows the product privacy policy. Personal residuals are not
exported to third parties.

## 10. Rollback plan

| Scenario | Rollback |
|---|---|
| L2 degrades warm-start MAE | Disable L2, keep L1 |
| L1 degrades warm-start MAE | Disable L1, serve L0 |
| Global model degrades | Serve score-history baseline |
| Feature pipeline breaks | Serve baseline with `insufficient_data` |
| Calibration intervals miscalibrated | Widen to the last validated width |

Rollback is a configuration change, not a redeploy. The baseline path must be
exercised in staging before launch.

## 11. Open items

| Item | Status | Owner |
|---|---|---|
| Fix `N_min`, `N_refit`, `alpha`, `k`, and caps on pilot data | [TBD] | ML |
| Define per-student "worse" threshold for the acceptance gate | [TBD] | ML + product |
| Specify the calibration-curve bins and minimum bin size | [TBD] | ML |
| Agree drift thresholds with the monitoring stack | [TBD] | ML + platform |
| Decide whether L2 is worth the complexity | [TBD] | ML |
| Write the student-facing copy for each confidence label | [TBD] | Product |
| Confirm retention period for prediction logs | [TBD] | Privacy |
