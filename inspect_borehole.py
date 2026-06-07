import pandas as pd
import sys

fpath = r'D:\1000_SCRIPTS\001_PreQE_Scripts\MultiLayerCompactionMonitoringWells\MLCW_Data_Extraction\YL_WSYL23G1_TUKU_土庫.xlsx'
xl = pd.ExcelFile(fpath)
print("Sheets:", xl.sheet_names)
for sh in xl.sheet_names:
    df = xl.parse(sh, header=None)
    print(f"\n=== Sheet: {sh!r} | shape: {df.shape} ===")
    print(df.to_string())
