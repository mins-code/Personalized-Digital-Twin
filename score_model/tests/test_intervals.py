"""Self-check for the conformal range helpers: python tests/test_intervals.py"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from oulad_benchmark import apply_intervals, conformal_halfwidths  # noqa: E402

rng = np.random.default_rng(0)
n = 20000
groups = rng.choice(["A", "B", "tiny"], size=n, p=[0.6, 0.395, 0.005])
noise = np.where(groups == "A", 5.0, 15.0)  # B is three times noisier than A
cal_err, test_err = rng.normal(0, noise), rng.normal(0, noise)
pred = np.full(n, 50.0)

w = conformal_halfwidths(np.abs(cal_err), groups, level=0.8)
assert "tiny" not in w, "groups under MIN_GROUP_ROWS must fall back to pooled width"
assert w["B"] > 2.5 * w["A"], w
lo, hi = apply_intervals(pred, groups, w)
inside = (50 + test_err >= lo) & (50 + test_err <= hi)
for g in ["A", "B"]:
    cov = inside[groups == g].mean()
    assert 0.78 < cov < 0.82, (g, cov)
assert apply_intervals(np.array([1.0, 99.0]), np.array(["A", "A"]), w)[0][0] == 0.0  # clipped
print("ok", {k: round(v, 2) for k, v in w.items()})
