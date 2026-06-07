import pandas as pd
df = pd.read_parquet(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\results\ring_gwl_xcorr\TUKU_ring_gwl_xcorr.parquet')
print('Columns:', df.columns.tolist())
print('\n---UNIQUE RING DEPTHS (ring_depth_m)---')
print(sorted(df['ring_depth_m'].unique()))
print('\n---UNIQUE WELL CODES---')
print(sorted(df['gwl_wellcode'].unique()))
print('\n---xcorr_max > 0.5---')
strong = df[df['xcorr_max'] > 0.5].copy()
print(f'Count: {len(strong)}')
print(strong[['ring_depth_m','gwl_station','gwl_wellcode','screen_mid_m','dist_m','xcorr_max','lag_days_at_max','pearson_r']].sort_values('xcorr_max', ascending=False).head(40).to_string())
print('\n---BEST PAIR PER ring_depth_m---')
best_per_ring = df.loc[df.groupby('ring_depth_m')['xcorr_max'].idxmax()]
print(best_per_ring[['ring_depth_m','gwl_station','gwl_wellcode','screen_mid_m','dist_m','xcorr_max','lag_days_at_max','pearson_r']].sort_values('ring_depth_m').to_string())
print('\n---NEGATIVE lags in strong pairs (head LAGS compaction, head leads compaction)---')
neg_lag = strong[strong['lag_days_at_max'] < 0]
print(f'Negative lag count: {len(neg_lag)}')
print(neg_lag[['ring_depth_m','gwl_station','gwl_wellcode','screen_mid_m','xcorr_max','lag_days_at_max']].sort_values('xcorr_max', ascending=False).head(20).to_string())
print('\n---POSITIVE lags in strong pairs---')
pos_lag = strong[strong['lag_days_at_max'] > 0]
print(f'Positive lag count: {len(pos_lag)}')
print(pos_lag[['ring_depth_m','gwl_station','gwl_wellcode','screen_mid_m','xcorr_max','lag_days_at_max']].sort_values('xcorr_max', ascending=False).head(20).to_string())
