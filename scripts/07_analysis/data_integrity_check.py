import pandas as pd
import os
import sys

# Paths
XL_PATH = r"data\mlcw\MLCW_InSAR_GWL_pairs.xlsx"
ASSIGN_CSV = r"D:\112_PROJECT_002\notes\dataset\gwl_to_mlcw_layer_assignment.csv"
FEATHER_DIR = r"data\gwl\well_timeseries"
CLASSIFY_DIR = r"data\mlcw\group_byLayer_reconstr"

def run_checks():
    print("=== DATA INTEGRITY & READINESS CHECK ===")
    if not os.path.exists(XL_PATH):
        print(f"Error: {XL_PATH} not found.")
        return

    df_xl = pd.read_excel(XL_PATH)
    print(f"Total MLCW Stations in Excel: {len(df_xl)}")

    # 1. Check Co-location vs Proxy
    proxies = df_xl[df_xl['Ename'] != df_xl['gwl_feather_stem']]
    print(f"Stations using Proxy (Name Mismatch): {len(proxies)}")

    # 2. Verify Feather Files & Well ID Consistency
    print("\n--- Feather File Verification ---")
    mismatches = []
    for _, row in df_xl.iterrows():
        ename = row['Ename']
        stem = row['gwl_feather_stem']
        xl_wells_raw = str(row['gwl_well_ids'])
        
        if pd.isna(stem):
            print(f"❌ {ename:15} | STEM MISSING")
            continue
            
        f_path = os.path.join(FEATHER_DIR, f"{stem}_gwl_timeseries.feather")
        if not os.path.exists(f_path):
            print(f"❌ {ename:15} | File NOT FOUND: {stem}_gwl_timeseries.feather")
            continue
            
        try:
            f_df = pd.read_feather(f_path)
            f_wells = [str(c).zfill(8) for c in f_df.columns if c != 'datetime']
            xl_wells = [w.strip().zfill(8) for w in xl_wells_raw.split(';') if w.strip() and w.strip() != 'nan']
            
            missing = [w for w in xl_wells if w not in f_wells]
            if missing:
                mismatches.append(f"{ename} ({stem}) missing wells in feather: {missing}")
        except Exception as e:
            print(f"🔥 {ename:15} | READ ERROR: {str(e)}")

    if mismatches:
        print("\n⚠️ WARNING: Found naming/ID discrepancies in feathers:")
        for m in mismatches:
            print(f"  {m}")
    else:
        print("✅ All feather headers match Excel well IDs.")

    # 3. Check Layer Assignment Coverage
    if os.path.exists(ASSIGN_CSV):
        df_assign = pd.read_csv(ASSIGN_CSV)
        assigned = df_assign[df_assign['assigned_wellcode'].notna()]['station'].unique()
        unassigned = [s for s in df_xl['Ename'] if s not in assigned]
        print(f"\nStations with physical screen assignments: {len(assigned)}")
        print(f"Stations needing proxy head: {len(unassigned)}")
    else:
        print(f"\n⚠️ Assignment CSV not found at {ASSIGN_CSV}")

    print("\nCheck complete.")

if __name__ == "__main__":
    run_checks()
