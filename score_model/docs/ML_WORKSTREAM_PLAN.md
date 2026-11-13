<!-- Paths below are relative to score_model/. -->
# CogniSync — ML Workstream Plan (Mine, no fatigue)

**Scope owner:** you (ML)  
**Excluded (teammates):** fatigue model + readiness display — M17/M18 (Zenodo/MMASH/PAAWS). Do not touch.
**Datasets used (PRD Section 8.2):** OULAD (benchmark only) + CogniSync-collected quiz/session records (future). Newsela/WikiLarge support simplification experiments only, never quiz prediction.

---

## 1. What I'm responsible for (PRD model inventory)

| ID | Component | My contribution | Training data |
|---|---|---|---|
| M1–M2 | OULAD baselines (historical mean, last score) | Compute + report | OULAD |
| M3–M5 | OULAD Ridge / Random Forest / XGBoost | Train + evaluate | OULAD |
| M6–M8 | CogniSync next-quiz score (Ridge/RF/XGBoost) | Train + compare | CogniSync quiz records (+ future features) |
| M9–M11 | Delayed retention (Ridge/RF/XGBoost) | Train + evaluate | CogniSync delayed-quiz records |
| M12 | Personalisation (per-student residual calibration) | Implement + validate | CogniSync quiz outcomes |
| M13 | Textbook meaning checker | Use pretrained NLI, evaluate | Separate human-labelled set (not PRD datasets) |
| M14–M16 | Workload, commute, recommendation | Rule-based engine + model-based ranking | Deterministic + future prediction outputs |
| M17–M18 | **Fatigue / readiness** | 🚫 TEAMMATES ONLY — not mine | Zenodo / MMASH / PAAWS |

---

## 2. Datasets I will use

### Primary — OULAD (offline benchmark only)
- Files: `assessments.csv`, `courses.csv`, `studentAssessment.csv`, `studentInfo.csv`, `studentRegistration.csv`, `OULAD.names`
- `studentVle.csv` (daily clicks) **is** in the team's dataset zip, although PRD v1.2 §8.2 says it was not uploaded. It is used as an optional engagement feature group (`--with-vle`) so the OULAD benchmark can run the PRD's core score-only vs. context-aware comparison. `vle.csv` (resource metadata) is not used. No fatigue labels, no stress/mood.
- Constraint: OULAD is a **benchmark only** — never deployed as the CogniSync model.

### Future (not yet collected) — CogniSync data
- Quiz attempts with topic/score/timestamp + preceding study-session IDs
- Delayed quiz outcomes (same topic, later timestamp)
- Optional authorised sleep/activity features (if student opts in later)
- Student-level records (pseudonymous IDs) kept isolated in evaluation

### Not mine, NOT used by me
- Student Lifestyle Dataset — excluded from training (PRD 8.2)
- SciQ-style Parquet — excluded (PRD 8.2)
- Newsela/WikiLarge — supported as simplification-pair experiments only; their edit labels are NOT factual-entailment labels, so they cannot substitute for the human-labelled meaning-checker eval set
- Zenodo/MMASH/PAAWS — fatigue workstream

---

## 3. What I will do (step-by-step plan)

### Step 1 — OULAD data audit & prep (1 session)
- Load `studentAssessment.csv`, `studentInfo.csv`, `courses.csv`, `assessments.csv`, `studentRegistration.csv`, `OULAD.names`
- Parse: eligible score records (not null, not banked), course/presentation keys, dates
- `studentVle.csv` is available; engagement features are optional (`--with-vle`) and reported as a separate run
- Build chronological, student-referenced training rows
- Deliverable: cleaned OULAD benchmark table (one row per prior-assessment window)

### Step 2 — OULAD baselines (M1, M2)
- Historical mean predictor
- Last-score predictor
- Report MAE/RMSE on a student-cleaved chronological split
- Use as the floor for all further benchmarks

### Step 3 — OULAD trainable benchmarks (M3, M4, M5)
- Ridge Regression
- Random Forest Regressor
- XGBoost Regressor
- Candidate features: previous score, historical mean, score trend, score variance, attempt count, assessment type, assessment weight, days to assessment, course/presentation context, registration/withdrawal status (all known before target)
- Compare every candidate against historical-mean and last-score baselines
- Deliverable: benchmark report (MAE/RMSE/R² + error distribution by assessment type and course/presentation)

### Step 4 — Next-quiz score model (M6, M7, M8) — when CogniSync data arrives
- Only after consented quiz/session records exist
- Baselines: last-score (same topic), topic-mean, overall student mean (labelled when topic history missing)
- Candidates: Ridge / Random Forest / XGBoost
- Compare: score-only model vs context-aware model (study history + workload + optional sleep/activity + commute); ablation to measure incremental value of each feature group
- Time-aware split (by quiz timestamp), student-level holdout — never random row split

### Step 5 — Delayed retention model (M9, M10, M11)
- Train only after delayed-quiz records exist (initial quiz + later, distinct quiz on same topic)
- Targets: delayed quiz score; baselines: most recent immediate score for that topic, mean of previous delayed scores, optional decay baseline
- Same chronological split + feature-group ablations as Step 4

### Step 6 — Personalisation (M12)
- Start: shared model with per-student bias correction (running/exponentially-weighted residual: predicted − actual)
- Threshold: only personalise after enough observations per student (configurable N, e.g. 5–10)
- Evaluate: global → shared+calibrated → personal refit, chronologically
- Deliverable: per-student calibration curve + drift monitoring

### Step 7 — Recommendation ranking (M16)
- Availability filter (classes, exams, deadlines, commute, blocked time)
- Score candidate windows with the validated next-quiz model (or score-history baseline when data thin)
- Transparent fallback when confidence/history insufficient
- No ML model for the engine itself — ranking is scoring + scheduling

### Step 8 — Evaluation protocol (all steps)
- Metrics: MAE, RMSE, R² where meaningful; calibration for probability-style outputs
- Splits: chronological, student-aware (no random row splitting; no future leak into features)
- Baselines reported against history mean + last score on every model
- Feature ablation recorded for each model

---

## 4. Deliverable checklist (what gets produced)

1. `docs/benchmarks/M5_OULAD_report.md` — baselines + Ridge/RF/XGBoost results
2. `src/oulad_benchmark.py` — reproducible OULAD benchmark
3. `src/pipeline.py` — point-in-time feature generation + leakage test
4. `docs/plans/model_plan.md` — next-quiz + delayed-retention model plan (data-ready)
5. `docs/plans/personalisation.md` — calibration + drift policy
6. `docs/plans/recommender_plan.md` — ranking + fallback policy
7. `docs/benchmarks/evaluation_protocol.md` — metrics, splits, ablation template

---

## 5. Go / no-go gates

- **Go:** benchmark beats last-score baseline meaningfully and is reproducible.
- **No-go:** OULAD benchmark does not beat the simple last-score baseline → stop handcrafted features, re-scope, or collect CogniSync data.
- **Data readiness:** the next-quiz/retention model is **not shipped** until consented CogniSync quiz/session/quiz-outcome records exist. Score-only baseline ships first.

---

## 6. Risks

- **OULAD ≠ CogniSync quizzes** — benchmark only; never claim transfer
- **Sparse CogniSync data** — cold-start → score-history baseline + explicit uncertainty
- **Students disengage** — no quiz attempts → no retention labels; follow-up window is short, missingness reported
- **Feature drift** — version features, track drift, re-evaluate chronologically
- **Overclaiming** — no causal claims, no grade guarantees
