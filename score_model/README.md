# Score model (PRD M1–M16, excluding fatigue)

Laid out like `fatigue_model/`. The offline benchmark (M1–M5) runs on OULAD; OULAD is a benchmark only, not CogniSync quiz data. Plans for the CogniSync models (M6–M16) are in `docs/plans/`. Moved here from Pranav-kb006/El5thsem.

## Layout

| Path | What |
|---|---|
| `src/pipeline.py` | Point-in-time feature generation and the leakage test suite |
| `src/preprocessing.py` | Builds `data/processed/engineered_dataset.csv.gz` (one row per attempt, with a `split` column) |
| `src/eda.py` | Plots and `eda_report.txt` in `docs/eda/` |
| `src/oulad_benchmark.py` | Trains and evaluates M1–M5; writes the reports, results JSON and per-row predictions to `docs/benchmarks/` |
| `tests/test_intervals.py` | Self-check for the 80% prediction ranges |
| `docs/plans/`, `docs/ML_WORKSTREAM_PLAN.md` | Plans for next-quiz / retention models, personalisation and the recommender |

## Run (from the repo root)

Put the OULAD CSVs from the team dataset zip in `score_model/data/raw/oulad/` (git-ignored; `studentVle.csv` is ~450 MB), or pass `--data-dir`.

```bash
python score_model/src/preprocessing.py
python score_model/src/eda.py
python score_model/src/oulad_benchmark.py --out-json score_model/docs/benchmarks/oulad_results.json \
    --report score_model/docs/benchmarks/M5_OULAD_report.md \
    --out-preds score_model/docs/benchmarks/oulad_test_predictions.csv.gz
python score_model/src/oulad_benchmark.py --with-vle --out-json score_model/docs/benchmarks/oulad_results_vle.json \
    --report score_model/docs/benchmarks/M5_OULAD_report_vle.md \
    --out-preds score_model/docs/benchmarks/oulad_test_predictions_vle.csv.gz
python score_model/tests/test_intervals.py
```

Each benchmark run takes a few minutes (`--skip-leakage` for a quick one).

## Protocol

Features are built only from records before `deadline − 7 days`, never from the attempt being predicted. Split: train 2013B+2013J, val 2014B, test 2014J, with no student in two splits. Every model is compared with historical-mean and last-score baselines, and each prediction gets an 80% range. Current result: XGBoost test MAE 9.886, 23.8% better than last score; leakage suite passes.
