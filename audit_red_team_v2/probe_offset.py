import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
SEQ = ROOT / "tau_demo_TUKU" / "results" / "seq"
truth = pd.read_csv(ROOT / "data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv",
                    parse_dates=["datetime"]).sort_values("datetime")
bt = truth[(truth.datetime >= "2019-01-01") & (truth.datetime <= "2023-12-31")]

for sch in ["none", "annual", "semiannual"]:
    for layer in ["F2", "F3"]:
        pred = pd.read_csv(SEQ / sch / f"TUKU_{layer}_seq_timeseries.csv",
                           parse_dates=["date"]).sort_values("date")
        m = pd.merge_asof(
            bt[["datetime", layer]].dropna().sort_values("datetime"), pred,
            left_on="datetime", right_on="date", direction="nearest",
            tolerance=pd.Timedelta(days=3)).dropna(subset=["pred_mm"])
        res = m[layer].values - m["pred_mm"].values
        print(f"{sch}/{layer}: first res {res[0]:+.1f} mm "
              f"({m.datetime.iloc[0].date()}), last {res[-1]:+.1f} mm "
              f"({m.datetime.iloc[-1].date()}), mean {res.mean():+.1f}, "
              f"std {res.std():.1f}, max|res| excl first "
              f"{np.max(np.abs(res[1:])):.1f} mm, "
              f"n pointwise |res|>20mm: {int((np.abs(res) > 20).sum())}")

t18 = truth[(truth.datetime >= "2018-10-01")
            & (truth.datetime <= "2019-02-01")][["datetime", "F2", "F3"]]
print(t18.to_string(index=False))
