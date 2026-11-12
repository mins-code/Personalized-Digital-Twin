---
title: "Recommender Plan — Ranking and Fallback Policy"
doc_id: "plans/recommender-plan"
version: "1.0"
status: "draft"
owner: "ML workstream"
created: "2026-11-12"
last_updated: "2026-11-12"
scope: "M14–M16 — availability filtering, recommendation scoring, ranking"
related:
  - "plans/model_plan.md"
  - "plans/personalisation.md"
  - "benchmarks/evaluation_protocol.md"
---

# Recommender Plan — Ranking and Fallback Policy

This document defines how CogniSync turns availability and predictions into a
short, ranked list of study windows. The engine itself is **rule-based**:
scoring and scheduling, not a learned policy. The only learned inputs are the
next-quiz and retention predictions described in `model_plan.md`.

> **Promise:** recommend a feasible time to study, explain why, and say how
> confident the estimate is. Never schedule over a confirmed class, exam, or
> deadline. Never invent confidence when history is thin.

> **Numbers policy.** Utility weights, relevance labels, pilot targets, and
> act-on rates are `[TBD]` until measured. The worked example in Section 9 is
> explicitly synthetic and is not a benchmark or pilot result. No fabricated
> ranking metric is used to justify a design choice.

## 1. Scope and non-goals

| In scope | Out of scope |
|---|---|
| Availability filtering | Fatigue / readiness scoring (M17–M18) |
| Candidate window generation | Medical or mental-health advice |
| Scoring with predicted gain and confidence | Autonomous calendar edits without confirmation |
| Ranking and explanation | Dark-pattern engagement optimisation |
| Transparent fallback ladder | Grade guarantees |
| Offline and pilot evaluation | LLM-generated study plans |

## 2. Inputs

| Input | Source | Required | Freshness |
|---|---|---|---|
| Classes, exams, deadlines | Timetable / student-confirmed calendar | Yes | Before each ranking |
| Blocked times | Student preferences | Yes | Before each ranking |
| Commute windows | Optional, student-enabled | No | Per day |
| Candidate study windows | Scheduling engine | Yes | Generated per request |
| Predicted next-quiz score | Next-quiz model (M6–M8) | Preferred | Per request |
| Predicted delayed retention | Retention model (M9–M11) | Optional | Per request |
| Topic need | Upcoming assessments, weak topics | Yes | Per request |
| Student constraints | Max session length, preferred times | Yes | Stable |
| Confidence / data coverage | Model output contract | Yes | Per prediction |

If a required input is missing, the engine does not guess. It uses the fallback
ladder in Section 6 and states why.

## 3. Pipeline

```text
1. Load commitments        → classes, exams, deadlines, blocked times
2. Generate windows        → free intervals of usable length
3. Hard-filter             → remove conflicts and infeasible windows
4. Compute need            → topic urgency × weakness × assessment proximity
5. Score expected gain     → predicted score / retention delta vs doing nothing
6. Apply confidence        → shrink gain by evidence quality
7. Subtract cost           → session length, commute, time-of-day friction
8. Rank                    → deterministic score, tie-breakers
9. Explain                 → one reason per recommendation
10. Fallback if needed     → baseline or generic window, with reason
```

### 3.1 Hard constraints (never violated)

| Constraint | Rule |
|---|---|
| Confirmed commitments | Never recommend a window that overlaps a class, exam, or deadline |
| Blocked time | Never recommend a window the student marked unavailable |
| Minimum session length | Do not propose a window shorter than the configured minimum |
| Daily limit | Do not exceed the configured recommended minutes per day |
| Quiet hours | Respect the student's sleep / no-study window |
| Explicit rejection | A rejected window is not shown again for the same day |

These are filters, not penalties. A window that fails a hard constraint never
enters the ranking, no matter how high its predicted gain.

### 3.2 Candidate windows

A candidate is a contiguous free interval:

```text
window = (start, end, duration_minutes, day_type, commute_available)
```

The generator produces windows at a fixed granularity (e.g. 15 minutes) but only
keeps intervals of at least the minimum session length. Overlapping windows are
deduplicated so the top-k list does not contain the same time twice.

## 4. Ranking

### 4.1 Utility function

```text
U(w) = confidence(w) × [ w_need × need(w)
                       + w_gain × expected_gain(w)
                       + w_ret  × expected_retention_gain(w) ]
       − w_cost × cost(w)
```

| Term | Meaning | Proposed default weight |
|---|---|---:|
| `need(w)` | Urgency and weakness of the target topic | [TBD] |
| `expected_gain(w)` | Predicted score improvement vs not studying | [TBD] |
| `expected_retention_gain(w)` | Predicted retention improvement vs baseline decay | [TBD] |
| `confidence(w)` | Evidence quality from the model output | [TBD] |
| `cost(w)` | Duration, commute, time-of-day friction, context switching | [TBD] |

Weights are configuration, not learned parameters, and must be set with product
before launch **[TBD]**. Until then, the engine uses a documented, deterministic
ordering:

1. Deadline urgency (sooner first).
2. Weakest topic with an upcoming assessment.
3. Higher predicted gain.
4. Shorter commute / lower friction.
5. Earlier window in the day.

### 4.2 Gain definition

`expected_gain` must be defined against a **doing-nothing baseline**, not against
another student:

```text
expected_gain = predicted_score_after_study − predicted_score_without_study
```

The "after study" prediction is the model's estimate for the next quiz on the
topic. The "without study" prediction is the score-history baseline or the decay
baseline. If the model cannot produce both sides of the comparison, the gain is
`[TBD]` and the engine falls back to the urgency ordering.

Do not present a predicted score as a guaranteed outcome of attending a window.

### 4.3 Confidence

Confidence comes from the prediction contract:

| Level | Condition | Effect on ranking |
|---|---|---|
| `high` | Warm-start student, calibrated intervals, recent data | Full gain term |
| `medium` | Some history, intervals within tolerance | Gain term shrunk |
| `low` | Thin history or early calibration | Gain term heavily shrunk |
| `insufficient_data` | No usable history | Gain term = 0; fallback ordering |

Confidence shrinks the gain term; it never inflates it. A high predicted gain
from a low-confidence model cannot outrank a moderate gain from a
high-confidence model by much.

### 4.4 Tie-breakers

Deterministic and explainable:

1. Earlier deadline.
2. Higher topic weakness.
3. Lower session cost.
4. Earlier start time.
5. Stable hash of `(student_id, date, window_start)` for fairness across
   otherwise identical candidates.

Tie-breakers must be stable for the same request so the UI does not reshuffle
between refreshes.

## 5. Explanation policy

Every recommendation includes one short reason and one confidence sentence.
The wording below is illustrative copy, not measured student data.

| Basis | Example explanation |
|---|---|
| Topic history | "You scored 62% on Fractions last time; this 40-minute window is before Thursday's quiz." |
| Overall history | "Your recent quiz average is 71%; this is your longest free window before the deadline." |
| Cold start | "We do not have enough quiz history yet, so this is based on your deadlines and available time." |
| Fallback | "The prediction service is unavailable, so this is the earliest feasible window before your deadline." |

Rules:

- The explanation must match the actual basis used for ranking.
- Do not show a predicted score without an interval or confidence label.
- Do not use urgency language that implies a guarantee ("You will pass if...").
- Do not compare the student to peers.
- Do not mention excluded data (mood, stress, fatigue).

## 6. Fallback ladder

The fallback ladder is a first-class feature, not an error path. Each level is
explicit, logged, and visible to the student.

| Level | Trigger | Ranking basis | Student-facing state |
|---|---|---|---|
| F0 — Full model | Next-quiz model available, warm start, calibrated | Predicted gain + need + cost | "Personalised for your history" |
| F1 — History baseline | Model unavailable or thin topic history | Last score / topic mean / overall mean | "Based on your recent quiz scores" |
| F2 — Rules only | No usable quiz history | Deadline urgency + available time | "Based on your deadlines and free time" |
| F3 — Generic windows | Scheduling or model service degraded | Earliest feasible windows | "Showing general study windows" |
| F4 — Insufficient data | No timetable or no feasible window | No recommendation | "Add your timetable or free up time" |

Rules:

- Never silently upgrade to a higher level. The level is part of the response.
- Never show F0 copy when F1–F3 produced the ranking.
- F4 is a valid outcome. Do not fill the screen with fake recommendations.
- When the model recovers, the next request returns to F0 automatically, but the
  UI does not rewrite history.

### 6.1 Degraded-mode behaviour

| Failure | Response |
|---|---|
| Next-quiz model timeout | Serve F1 with cached baseline; log timeout |
| Timetable sync failure | Use last confirmed timetable; mark it stale |
| Commute data missing | Treat commute as unavailable; do not guess |
| Calendar conflict detected | Re-filter; never recommend over the conflict |
| All windows infeasible | Return F4 with the reason |
| Feature schema mismatch | Disable model; serve F1/F2 |

## 7. Cold start

A new student has no quiz history. The engine must still be useful:

1. Ask for timetable and study preferences during onboarding.
2. Rank by deadline urgency and available time (F2).
3. After each quiz, the next-quiz model becomes eligible.
4. Enable confidence-weighted gain only when the model reports at least
   `medium` confidence.
5. Never show a personalised score prediction to a cold-start student.

The cold-start experience is a product requirement, not a model edge case.

## 8. Evaluation

### 8.1 Offline replay

Replay logged requests against the current ranker:

| Metric | Definition | Role |
|---|---|---|
| NDCG@3 | Normalised discounted gain of top 3 windows | Primary offline metric |
| Recall@3 | Share of relevant windows in top 3 | Coverage |
| MRR | Rank of the first relevant window | How early the best option appears |
| Coverage | Share of requests with at least one F0/F1 recommendation | Fallback health |
| Fallback share | Share of requests served by each level | Degradation visibility |
| Determinism | Same request produces the same ranking | Trust / debuggability |

Relevance labels are **[TBD]**. Proposed definitions: the student accepted the
window; the student completed a session; the session led to a quiz attempt on
the targeted topic. Pick one before evaluation and keep it fixed.

### 8.2 Pilot evaluation

| Metric | Target | Status |
|---|---|---|
| Act-on rate within 24 h | Beat time-of-day and soonest-free-slot heuristics | [TBD] |
| Session completion rate | No degradation vs baseline | [TBD] |
| Recommendation acceptance | [TBD] | [TBD] |
| Student-reported usefulness | [TBD] | [TBD] |
| Drop-off after first recommendation | [TBD] | [TBD] |
| Conflict rate (recommended over a commitment) | 0 | [TBD] |

The product-level gate comes from the project plan: if the engine cannot beat the
simple heuristics in the pilot, ship the heuristics.

### 8.3 Guardrail metrics

| Guardrail | Why |
|---|---|
| Recommended minutes per day | Prevent over-scheduling |
| Late-night recommendation share | Protect sleep and quiet hours |
| Topic repetition rate | Avoid recommending the same topic every time |
| Explanation mismatch rate | Ensure copy matches the basis |
| Fallback label accuracy | Prevent false personalisation claims |

## 9. Worked example

> Illustrative only. The scores, windows, and confidence values below are
> synthetic, not benchmark or pilot results.

Input:

- Thursday quiz on Fractions, student score history: 62% on the topic.
- Free windows: Tuesday 18:00–18:40, Wednesday 07:30–08:00, Wednesday 19:00–20:00.
- Wednesday 07:30 is before a confirmed 08:30 class; commute data is unavailable.
- Model confidence: `medium` (6 observations).

Ranking:

| Rank | Window | Why |
|---|---|---|
| 1 | Tuesday 18:00–18:40 | Longest free window before the quiz; topic history available; medium confidence |
| 2 | Wednesday 19:00–20:00 | Later but longer; lower urgency |
| 3 | Wednesday 07:30–08:00 | Short and adjacent to a class; higher friction |

The copy says "Based on your recent quiz scores", not "You will improve by 8
points". The interval is shown because confidence is only medium.

## 10. Logging

For each request, log:

```yaml
request_id: "[TBD]"
student_id_hash: "[TBD]"
timestamp: "[TBD]"
candidate_windows: "[TBD]"
hard_filter_rejections: "[TBD]"
ranking_level: "F0 | F1 | F2 | F3 | F4"
model_version: "[TBD]"
feature_version: "[TBD]"
prediction_confidence: "[TBD]"
utility_terms: "[TBD]"   # need, gain, retention, cost, confidence
top_k: "[TBD]"
explanation_basis: "[TBD]"
```

Logs support offline replay and drift analysis. They do not contain raw calendar
content beyond what is needed to reproduce the ranking.

## 11. Guardrails and ethics

- **No dark patterns.** No fake urgency, no streak pressure, no "everyone else
  is studying" comparisons.
- **No autonomous calendar edits.** Recommendations require confirmation.
- **No medical or fatigue claims.** Readiness is a separate, teammate-owned
  surface.
- **No hidden data use.** The student can see which inputs produced the ranking.
- **No over-scheduling.** Daily caps and quiet hours are hard constraints.
- **No ranking of students.** The engine ranks windows, not people.
- **Accessibility.** Time and duration must be screen-reader friendly; colour is
  never the only signal.

## 12. Open items

| Item | Status | Owner |
|---|---|---|
| Fix utility weights | [TBD] | ML + product |
| Define the relevance label for offline replay | [TBD] | ML + product |
| Set daily recommended-minutes cap | [TBD] | Product |
| Decide whether commute data is in the MVP | [TBD] | Product |
| Define the minimum session length | [TBD] | Product |
| Build the offline replay harness | [TBD] | ML |
| Agree fallback copy for each level | [TBD] | Product + design |
| Validate that F2 beats the soonest-free-slot heuristic | [TBD] | ML |
