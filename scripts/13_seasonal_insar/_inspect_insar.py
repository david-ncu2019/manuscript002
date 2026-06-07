import pandas as pd
df = pd.read_feather('data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather')
print('Shape:', df.shape)
print('First 10 cols:', list(df.columns[:10]))
print('Last 5 cols:', list(df.columns[-5:]))
print('Ename sample:', df['Ename'].head(5).tolist())
print('Code sample:', df['Code'].head(5).tolist())
# Find TUKU row
for col in ['Ename','Code']:
    hits = df[df[col] == 'TUKU']
    print(f"TUKU in '{col}':", len(hits), "rows")
