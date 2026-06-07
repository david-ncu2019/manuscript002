import sys
from pathlib import Path
sys.path.insert(0, r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\scripts\10_ihmf')
from ihmf_io_multilayer import load_all_layers, load_config
import numpy as np

ROOT = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2')
shared_cfg, entries, insar_csv = load_config(ROOT)
layer_dfs, layer_metas, insar_mm = load_all_layers('TUKU', entries, ROOT, insar_csv)

print('=== TUKU data diagnostics ===')
for layer, df in layer_dfs.items():
    print(f'{layer}: T={len(df)} epochs, {df["datetime"].min().date()} -> {df["datetime"].max().date()}')
    inc_dH = np.diff(df["head_m"].values)
    print(f'  inc_dH length={len(inc_dH)}, mean={inc_dH.mean():.4f} m/epoch')

print(f'\nInSAR: len={len(insar_mm)}, min={insar_mm.min():.2f} mm, max={insar_mm.max():.2f} mm')
print(f'InSAR units check (should be mm ~-50 to -300): ok={abs(insar_mm.min()) > 10}')

# Check what tau_opt the v3 tau search returns for F2
from ihmf_model_v3 import build_regime_mask, tau_grid_search_per_layer
df = layer_dfs['F2']
meta = layer_metas['F2']
inc_dH = np.diff(df["head_m"].values)
inc_db = np.diff(df["mlcw_mm"].values)
e_m, i_m = build_regime_mask(df["head_m"].values[:-1], meta["h_c_head_m"])
tau_opt, rss_curve, _ = tau_grid_search_per_layer(inc_dH, inc_db, e_m, i_m, 73, dates=df["datetime"].values[:-1])
T = len(inc_dH) - tau_opt
print(f'\nF2 tau_opt={tau_opt} ({tau_opt*5} days), T_after_lag={T}, full_inc_len={len(inc_dH)}')
print(f'RSS at tau_opt={rss_curve[tau_opt]:.6f}')
