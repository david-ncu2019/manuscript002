import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

def exponential_model(x, a, b):
    """
    Exponential model for subsidence: y = a * (exp(-b * x) - 1)
    - 'a' represents the ultimate displacement (plateau).
    - 'b' represents the decay/rate constant.
    - At x=0, y=0.
    """
    return a * (np.exp(-b * x) - 1)

def main():
    # 1. Setup paths
    csv_path = "XIGANG_ringbyring_timeseries.csv"
    if not os.path.exists(csv_path):
        print(f"Error: Could not find {csv_path}")
        return

    # 2. Load Data
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Identify columns (assuming first is date, second is displacement)
    date_col = df.columns[0]
    disp_col = df.columns[1]

    # Convert dates to datetime and then to days from start
    # format='%y/%m/%d' matches 97/5/19
    df[date_col] = pd.to_datetime(df[date_col], format='%y/%m/%d')
    df = df.sort_values(by=date_col)
    
    # Calculate x (days from start) and y (displacement in mm)
    start_date = df[date_col].iloc[0]
    df['days'] = (df[date_col] - start_date).dt.days
    
    x_data = df['days'].values
    y_data = df[disp_col].values * 1000  # Convert to mm if input is in meters

    # 3. Fit Model
    print("Fitting exponential model...")
    # Initial guesses: a=100 (plateau at 100mm), b=0.001
    p0 = [100, 0.001]
    
    try:
        popt, pcov = curve_fit(exponential_model, x_data, y_data, p0=p0)
        a_fit, b_fit = popt
        
        # Calculate time constant Tau (days to reach ~63% of total)
        tau = 1 / b_fit if b_fit != 0 else np.inf
        
        print("\n" + "="*30)
        print("FIT RESULTS")
        print("="*30)
        print(f"Model: y = a * (exp(-b * x) - 1)")
        print(f"Ultimate Subsidence (a): {a_fit:.2f} mm")
        print(f"Decay Constant (b):      {b_fit:.6f}")
        print(f"Time Constant (Tau):     {tau:.1f} days")
        print("="*30)

        # 4. Generate fitted curve for plotting
        x_fine = np.linspace(x_data.min(), x_data.max(), 500)
        y_fit = exponential_model(x_fine, *popt)

        # 5. Visualize
        plt.figure(figsize=(10, 6))
        plt.plot(df[date_col], y_data, 'ko', markersize=4, alpha=0.5, label='Observed Data')
        plt.plot(pd.to_datetime(x_fine, unit='D', origin=start_date), y_fit, 'r-', linewidth=2, label='Exp Fit')
        
        plt.title(f"Exponential Fit: {disp_col} (XIGANG)")
        plt.xlabel("Date")
        plt.ylabel("Displacement (mm)")
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.legend()
        
        save_name = f"exponential_fit_{disp_col}.png"
        plt.savefig(save_name, dpi=300)
        print(f"Plot saved to: {save_name}")
        # plt.show()

    except Exception as e:
        print(f"Fitting failed: {e}")

if __name__ == "__main__":
    main()
