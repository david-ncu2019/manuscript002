import pandas as pd
import numpy as np

# Read stations
df = pd.read_csv('7_interpolation/gridpnt_crfp_500m_utm50.csv')
x_min = df['X_UTM50N'].min() - 5000
x_max = df['X_UTM50N'].max() + 5000
y_min = df['Y_UTM50N'].min() - 5000
y_max = df['Y_UTM50N'].max() + 5000

print(f"Bounding box (buffered by 5km):")
print(f"Y (North): {y_min:.1f} to {y_max:.1f}")
print(f"X (East): {x_min:.1f} to {x_max:.1f}")

# Print subset command
print("\nRun this command:")
print(f"subset.py merged_202604/6_decompose/vert_regts_msk.h5 -l {y_min:.1f} {y_max:.1f} {x_min:.1f} {x_max:.1f} -o merged_202604/6_decompose/sub_vert_timeseries_msk.h5")
