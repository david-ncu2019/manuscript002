"""Quality check summary for 2S-TOOL batch run."""
import pandas as pd
import numpy as np

df = pd.read_csv("data/gwl/2stool_outputs/2stool_results_summary.csv")

n_ok = int((df["skv"] > 0).sum())
n_neg = int((df["skv"] <= 0).sum())
n_errors = 13  # from batch log

print(f"Total processed: {len(df)}")
print(f"OK (S_kv > 0):         {n_ok}")
print(f"NEG_SKV (S_kv <= 0):   {n_neg}")
print(f"ERROR (not in output): {n_errors}")
print()

skv_all = df["skv"]
print(f"S_kv range (all 182): {skv_all.min():.4e} to {skv_all.max():.4e}")
ok_df = df[df["skv"] > 0]
print(f"S_kv range (OK only): {ok_df['skv'].min():.4e} to {ok_df['skv'].max():.4e}")
print()

# NEG_SKV list
neg_df = df[df["skv"] <= 0][["station", "layer", "skv"]].sort_values("skv")
print(f"NEG_SKV stations ({len(neg_df)}):")
print(neg_df.to_string(index=False))

print()
print("=== TUKU reference check ===")
tuku = df[df["station"] == "TUKU"].sort_values("layer")
for _, row in tuku.iterrows():
    print(f"  {row['layer']:3s}: S_kv={row['skv']:.4e}  S_ke_w={row['ske_weighted']:.4e}  n_accepted={int(row['n_accepted_loops'])}")

print()
print("TUKU T2: ERROR (SVD did not converge) — not in summary")
