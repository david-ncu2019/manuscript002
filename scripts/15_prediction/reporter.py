"""
Output writing — CSVs and figures. No computation.
All figures: A4 landscape (11.7 × 8.3 in), 300 dpi, bbox_inches='tight'.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

A4_W, A4_H, DPI = 11.7, 8.3, 300
LAYERS_ORDER = ['F1', 'T1', 'F2', 'T2', 'F3', 'F4']


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


# ── CSV writers ───────────────────────────────────────────────────────────────

def write_walkforward_csv(results: pd.DataFrame, output_dir: Path) -> None:
    _ensure(output_dir)
    path = output_dir / 'walkforward_rmse.csv'
    results.to_csv(path, index=False)
    print(f"  Saved → {path.name}  ({len(results)} rows)")


def write_comparison_csv(results: pd.DataFrame, output_dir: Path) -> None:
    """Per-station per-layer median skill across folds."""
    _ensure(output_dir)
    grp = results.groupby(['station', 'layer'], sort=False).agg(
        median_skill_tier1_vs_persistence=('skill_tier1_vs_persistence', 'median'),
        median_skill_tier1_vs_trend=('skill_tier1_vs_trend', 'median'),
        median_skill_tier2_vs_persistence=('skill_tier2_vs_persistence', 'median'),
        median_skill_tier2_vs_trend=('skill_tier2_vs_trend', 'median'),
        n_folds=('fold_year', 'count'),
    ).reset_index()
    path = output_dir / 'trackA_comparison.csv'
    grp.to_csv(path, index=False)
    print(f"  Saved → {path.name}  ({len(grp)} rows)")


def write_stations_skipped_csv(skipped: list[dict], output_dir: Path) -> None:
    _ensure(output_dir)
    path = output_dir / 'stations_skipped.csv'
    pd.DataFrame(skipped).to_csv(path, index=False)
    print(f"  Saved → {path.name}  ({len(skipped)} skipped stations)")


def write_spatial_loo_csv(results: pd.DataFrame, output_dir: Path) -> None:
    _ensure(output_dir)
    path = output_dir / 'spatial_loo_cv.csv'
    results.to_csv(path, index=False)
    print(f"  Saved → {path.name}  ({len(results)} rows)")


def write_grid_fbar_csv(results: pd.DataFrame, output_dir: Path) -> None:
    _ensure(output_dir)
    path = output_dir / 'grid_fbar_kriged.csv'
    results.to_csv(path, index=False)
    print(f"  Saved → {path.name}  ({len(results)} rows)")


# ── Figure writers ────────────────────────────────────────────────────────────

def plot_walkforward_heatmap(results: pd.DataFrame, output_dir: Path) -> None:
    """
    Heatmap of skill_tier1_vs_trend: rows = stations, cols = layers × folds.
    Color: green = improvement, red = degradation, white = 0.
    """
    _ensure(output_dir / 'figures')
    if results.empty:
        return

    stations = sorted(results['station'].unique())
    layers   = [l for l in LAYERS_ORDER if l in results['layer'].unique()]
    folds    = sorted(results['fold_year'].unique())

    # Columns: layer_fold pairs
    col_labels = [f"{l}\n{y}" for l in layers for y in folds]
    n_rows = len(stations)
    n_cols = len(col_labels)

    mat = np.full((n_rows, n_cols), np.nan)
    for i, stn in enumerate(stations):
        for j, (lyr, yr) in enumerate([(l, y) for l in layers for y in folds]):
            sub = results[(results['station'] == stn) &
                          (results['layer'] == lyr) &
                          (results['fold_year'] == yr)]
            if not sub.empty:
                mat[i, j] = float(sub['skill_tier1_vs_trend'].iloc[0])

    fig, ax = plt.subplots(1, 1, figsize=(max(A4_W, 0.6 * n_cols), max(A4_H, 0.3 * n_rows)), dpi=DPI)
    cmap = plt.get_cmap('RdYlGn')
    norm = mcolors.TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0)
    im = ax.imshow(mat, cmap=cmap, norm=norm, aspect='auto')
    plt.colorbar(im, ax=ax, label='Skill score (1 − RMSE/RMSE_trend)')
    ax.set_xticks(range(n_cols)); ax.set_xticklabels(col_labels, fontsize=7, rotation=45, ha='right')
    ax.set_yticks(range(n_rows)); ax.set_yticklabels(stations, fontsize=8)
    ax.set_title('Walk-forward skill: Tier 1 vs trend-extrapolation baseline', fontsize=11)
    fig.tight_layout()
    path = output_dir / 'figures' / 'walkforward_skill_heatmap.png'
    fig.savefig(path, dpi=DPI, bbox_inches='tight', format='png')
    plt.close(fig)
    print(f"  Saved → figures/walkforward_skill_heatmap.png")


def plot_spatial_fbar_maps(grid_fbar: pd.DataFrame, layer: str, output_dir: Path) -> None:
    """Scatter map of kriged fbar at 8,577 grid points for one layer."""
    _ensure(output_dir / 'figures')
    sub = grid_fbar[grid_fbar['layer'] == layer]
    if sub.empty:
        return
    fig, ax = plt.subplots(1, 1, figsize=(A4_W, A4_H), dpi=DPI)
    sc = ax.scatter(sub['X_TWD97'], sub['Y_TWD97'], c=sub['fbar_kriged'],
                    cmap='viridis', s=4, vmin=0)
    plt.colorbar(sc, ax=ax, label=f'f̄_k ({layer}) — kriged')
    ax.set_xlabel('X TWD97 (m)'); ax.set_ylabel('Y TWD97 (m)')
    ax.set_title(f'Kriged compaction fraction — layer {layer}', fontsize=11)
    ax.set_aspect('equal')
    fig.tight_layout()
    path = output_dir / 'figures' / f'spatial_fbar_map_{layer}.png'
    fig.savefig(path, dpi=DPI, bbox_inches='tight', format='png')
    plt.close(fig)
    print(f"  Saved → figures/spatial_fbar_map_{layer}.png")


def plot_loo_cv_error_map(loo_results: pd.DataFrame, output_dir: Path) -> None:
    """Scatter map of LOO-CV absolute error per station for one summary layer."""
    _ensure(output_dir / 'figures')
    if loo_results.empty:
        return
    # Summarise: mean absolute error across layers
    summ = loo_results.groupby('station').agg(
        X_TWD97=('X_TWD97', 'first'),
        Y_TWD97=('Y_TWD97', 'first'),
        mean_abs_error=('error_abs', 'mean'),
    ).reset_index()
    fig, ax = plt.subplots(1, 1, figsize=(A4_W, A4_H), dpi=DPI)
    sc = ax.scatter(summ['X_TWD97'], summ['Y_TWD97'],
                    c=summ['mean_abs_error'], cmap='YlOrRd', s=60,
                    vmin=0, edgecolors='k', linewidths=0.5)
    plt.colorbar(sc, ax=ax, label='Mean |fbar_actual − fbar_predicted|')
    ax.set_xlabel('X TWD97 (m)'); ax.set_ylabel('Y TWD97 (m)')
    ax.set_title('Spatial LOO-CV error map (ordinary kriging)', fontsize=11)
    ax.set_aspect('equal')
    for _, row in summ.iterrows():
        ax.annotate(row['station'], (row['X_TWD97'], row['Y_TWD97']),
                    fontsize=5, ha='center', va='bottom')
    fig.tight_layout()
    path = output_dir / 'figures' / 'loo_cv_error_map.png'
    fig.savefig(path, dpi=DPI, bbox_inches='tight', format='png')
    plt.close(fig)
    print(f"  Saved → figures/loo_cv_error_map.png")
