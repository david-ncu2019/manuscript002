"""Unit tests for the sequential-rehearsal core. Run:
$env:PYTHONPATH=""; conda run -n fafalab2 python -m pytest tau_demo_TUKU/seq/test_seq_core.py -v
"""
import numpy as np
import pandas as pd
import pytest
from time_oracle import TimeOracle, LeakageError
from conformal import ConformalBank

def _df():
    d = pd.date_range("2020-01-01", periods=100, freq="5D")
    return pd.DataFrame({"date": d, "v": np.arange(100.0)})

def test_oracle_blocks_future():
    df = _df()
    o = TimeOracle(pd.Timestamp("2020-03-01"))
    assert o.view(df)["date"].max() <= pd.Timestamp("2020-03-01")

def test_oracle_strict_raises():
    df = _df()
    o = TimeOracle(pd.Timestamp("2020-03-01"))
    with pytest.raises(LeakageError):
        o.assert_no_future(df.iloc[[-1]])

def test_oracle_no_backward():
    o = TimeOracle(pd.Timestamp("2020-03-01"))
    with pytest.raises(LeakageError):
        o.advance(pd.Timestamp("2020-01-01"))

def test_conformal_coverage_synthetic():
    rng = np.random.default_rng(0)
    bank = ConformalBank(alpha=0.10)
    for _ in range(500):
        bank.add("F1", horizon=10, abs_err=abs(rng.normal(0, 2.0)))
    hw = bank.half_width("F1", horizon=10)
    fresh = np.abs(rng.normal(0, 2.0, 5000))
    cov = float((fresh <= hw).mean())
    assert 0.85 <= cov <= 0.95   # 90% nominal

def test_conformal_insufficient_is_nan():
    bank = ConformalBank(alpha=0.10)
    bank.add("F1", horizon=10, abs_err=1.0)
    assert np.isnan(bank.half_width("F1", horizon=10))
