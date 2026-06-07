import pandas as pd
df = pd.read_parquet('results/ring_gwl_xcorr/TUKU_ring_gwl_xcorr.parquet')
print('Columns:', list(df.columns))
print('Rows:', len(df))
print('xcorr_max range:', df['xcorr_max'].min(), 'to', df['xcorr_max'].max())
deep = df[df['ring_depth_m'] > 150]
if 'lag_days_at_max' in df.columns:
    print('\nDeep rings top-10 by xcorr_max:')
    print(deep[['ring_depth_m','gwl_wellcode','lag_at_max','lag_days_at_max','xcorr_max']].sort_values('xcorr_max', ascending=False).head(10).to_string())
else:
    print('\nlag_days_at_max column MISSING')
    print(deep[['ring_depth_m','gwl_wellcode','lag_at_max','xcorr_max']].sort_values('xcorr_max', ascending=False).head(10).to_string())
