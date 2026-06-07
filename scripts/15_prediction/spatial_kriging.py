"""
Spatial kriging of f̄_k to 8,577 unmonitored grid points.
Uses TWD97 coordinates (X_TWD97, Y_TWD97) — the grid feather has no UTM columns.
Ordinary kriging only (zone-stratified kriging deferred — no zone CSV exists).
"""
import numpy as np
import pandas as pd
from pathlib import Path

try:
    from pykrige.ok import OrdinaryKriging
    PYKRIGE_AVAILABLE = True
except ImportError:
    PYKRIGE_AVAILABLE = False

_LAYERS_ORDER = ['F1', 'T1', 'F2', 'T2', 'F3', 'F4']


def _idw_interpolate(x_st: np.ndarray, y_st: np.ndarray, v_st: np.ndarray,
                     x_gd: np.ndarray, y_gd: np.ndarray,
                     power: float = 2.0) -> np.ndarray:
    """Inverse distance weighting fallback."""
    out = np.full(len(x_gd), np.nan)
    valid = ~np.isnan(v_st)
    if valid.sum() < 2:
        return out
    xs, ys, vs = x_st[valid], y_st[valid], v_st[valid]
    for i, (xg, yg) in enumerate(zip(x_gd, y_gd)):
        d = np.sqrt((xs - xg)**2 + (ys - yg)**2)
        d = np.maximum(d, 1.0)
        w = 1.0 / d**power
        out[i] = float(np.sum(w * vs) / np.sum(w))
    return out


def krige_fbar_to_grid(
    station_fbar: pd.DataFrame,
    grid_coords: pd.DataFrame,
    method: str = 'ordinary',
) -> pd.DataFrame:
    """
    Interpolate f̄_k from MLCW stations to grid points.

    Parameters
    ----------
    station_fbar : DataFrame with columns [station, layer, fbar, X_TWD97, Y_TWD97]
    grid_coords  : DataFrame indexed by PointKey with columns [X_TWD97, Y_TWD97]
    method       : 'ordinary' | 'idw'

    Returns
    -------
    DataFrame with columns [grid_id, layer, fbar_kriged, fbar_std, X_TWD97, Y_TWD97]
    """
    rows = []
    layers = [l for l in _LAYERS_ORDER if l in station_fbar['layer'].unique()]

    for layer in layers:
        sub = station_fbar[station_fbar['layer'] == layer].dropna(subset=['fbar'])
        if len(sub) < 3:
            continue

        x_st = sub['X_TWD97'].values.astype(float)
        y_st = sub['Y_TWD97'].values.astype(float)
        v_st = sub['fbar'].values.astype(float)
        x_gd = grid_coords['X_TWD97'].values.astype(float)
        y_gd = grid_coords['Y_TWD97'].values.astype(float)

        fbar_kriged = np.full(len(x_gd), np.nan)
        fbar_std    = np.full(len(x_gd), np.nan)

        if method == 'ordinary' and PYKRIGE_AVAILABLE:
            try:
                ok = OrdinaryKriging(
                    x_st, y_st, v_st,
                    variogram_model='spherical',
                    enable_plotting=False, verbose=False,
                )
                z, ss = ok.execute('points', x_gd, y_gd)
                fbar_kriged = np.asarray(z).flatten()
                fbar_std    = np.sqrt(np.asarray(ss).flatten())
            except Exception as e:
                print(f"  WARNING: OrdinaryKriging failed for layer {layer}: {e}. Falling back to IDW.")
                fbar_kriged = _idw_interpolate(x_st, y_st, v_st, x_gd, y_gd)
        else:
            fbar_kriged = _idw_interpolate(x_st, y_st, v_st, x_gd, y_gd)

        for i, gid in enumerate(grid_coords.index):
            rows.append({
                'grid_id':     gid,
                'layer':       layer,
                'fbar_kriged': float(fbar_kriged[i]),
                'fbar_std':    float(fbar_std[i]) if not np.isnan(fbar_std[i]) else np.nan,
                'X_TWD97':     float(x_gd[i]),
                'Y_TWD97':     float(y_gd[i]),
            })

    return pd.DataFrame(rows)


def run_spatial_loo_cv(
    station_fbar: pd.DataFrame,
    method: str = 'ordinary',
) -> pd.DataFrame:
    """
    Leave-one-out cross-validation: hold out each station, krige from remaining N-1,
    compare predicted fbar to actual fbar.

    Parameters
    ----------
    station_fbar : DataFrame with columns [station, layer, fbar, X_TWD97, Y_TWD97]
    method       : 'ordinary' | 'idw'

    Returns
    -------
    DataFrame with columns [station, layer, fbar_actual, fbar_predicted, error_abs,
                             X_TWD97, Y_TWD97]
    """
    rows = []
    stations = station_fbar['station'].unique()
    layers   = [l for l in _LAYERS_ORDER if l in station_fbar['layer'].unique()]

    for layer in layers:
        sub = station_fbar[station_fbar['layer'] == layer].dropna(subset=['fbar'])
        if len(sub) < 4:
            continue

        for held_stn in stations:
            train = sub[sub['station'] != held_stn]
            test  = sub[sub['station'] == held_stn]
            if test.empty or len(train) < 3:
                continue

            x_st = train['X_TWD97'].values.astype(float)
            y_st = train['Y_TWD97'].values.astype(float)
            v_st = train['fbar'].values.astype(float)
            x_te = test['X_TWD97'].values.astype(float)
            y_te = test['Y_TWD97'].values.astype(float)

            pred = np.nan
            if method == 'ordinary' and PYKRIGE_AVAILABLE:
                try:
                    ok = OrdinaryKriging(
                        x_st, y_st, v_st,
                        variogram_model='spherical',
                        enable_plotting=False, verbose=False,
                    )
                    z, _ = ok.execute('points', x_te, y_te)
                    pred = float(np.asarray(z).flatten()[0])
                except Exception:
                    pred = _idw_interpolate(x_st, y_st, v_st, x_te, y_te)[0]
            else:
                pred = _idw_interpolate(x_st, y_st, v_st, x_te, y_te)[0]

            actual = float(test['fbar'].iloc[0])
            rows.append({
                'station':        held_stn,
                'layer':          layer,
                'fbar_actual':    round(actual, 5),
                'fbar_predicted': round(pred, 5) if not np.isnan(pred) else np.nan,
                'error_abs':      round(abs(pred - actual), 5) if not np.isnan(pred) else np.nan,
                'X_TWD97':        float(test['X_TWD97'].iloc[0]),
                'Y_TWD97':        float(test['Y_TWD97'].iloc[0]),
            })

    return pd.DataFrame(rows)
