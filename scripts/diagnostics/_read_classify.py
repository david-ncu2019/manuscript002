import pandas as pd
ct = pd.read_csv(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\mlcw\group_byLayer_reconstr\TUKU_classify_table.csv')
print('TUKU classify table:')
print(ct.to_string())
# Also look at first rows of reconst_grouped to see column names
rg = pd.read_csv(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\mlcw\group_byLayer_reconstr\TUKU_reconst_grouped.csv', nrows=3)
print('\nTUKU_reconst_grouped columns:', rg.columns.tolist())
print(rg.head(3).to_string())
