"""Preprocessing for the CogniSync score model benchmark (OULAD, PRD models M1-M5).

* Loads the raw OULAD CSVs (default ``score_model/data/raw/oulad``; ``--data-dir`` to override).
* Builds one row per scored, non-banked assessment attempt with point-in-time features:
  everything is computed from records strictly before ``deadline - 7 days``, and the
  target attempt never sees itself (see ``pipeline.py``).
* Adds the studentVle click features (needs ``studentVle.csv``).
* Splits chronologically by presentation with disjoint students
  (train 2013B+2013J, val 2014B, test 2014J) and keeps the split label.
* Missing values stay NaN; imputation happens at training time on train rows only.
* Writes ``data/processed/engineered_dataset.csv.gz``.
"""

import argparse
from pathlib import Path

import pandas as pd

import pipeline as pit

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "processed" / "engineered_dataset.csv.gz"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", default=pit.DATA_DIR, help="folder with the OULAD CSVs")
    args = parser.parse_args()

    pit.enable_vle_features()
    tables = pit.load_oulad(args.data_dir, with_vle=True)
    features = pit.build_features(tables)
    split = pit.chronological_student_split(features)
    print(split["audit"].to_string(index=False))

    parts = [part.assign(split=name) for name, part in split["splits"].items()]
    cols = ["id_student", "id_assessment", "split"] + pit.FEATURE_COLUMNS + ["score"]
    final = pd.concat(parts, ignore_index=True)[cols]
    assert final[["id_student", "id_assessment"]].duplicated().sum() == 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(OUT_PATH, index=False, float_format="%.4f")
    print(f"{len(features):,} scored attempts -> {len(final):,} rows with >=1 prior attempt; wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
