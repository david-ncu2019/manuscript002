import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set style for publication quality without seaborn
plt.style.use('seaborn-v0_8-ticks' if 'seaborn-v0_8-ticks' in plt.style.available else 'classic')
plt.rcParams.update({
    'axes.linewidth': 1.5,
    'xtick.major.width': 1.5,
    'ytick.major.width': 1.5,
    'xtick.minor.width': 1.5,
    'ytick.minor.width': 1.5,
    'axes.labelsize': 18,
    'axes.titlesize': 20,
    'legend.fontsize': 14,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
})

def load_and_convert(file_path):
    df = pd.read_csv(file_path)
    # Convert InSAR (Displacement) to cm/year
    df['InSAR_Velocity_cm_yr'] = df['Displacement'] * 10
    # Convert GPS/Leveling (Velocity) to cm/year
    df['Ref_Velocity_cm_yr'] = df['Velocity'] * 100
    return df

def plot_comparison(df, label, color, marker, out_prefix, add_labels=False):
    fig, ax = plt.subplots(figsize=(8, 8))
    
    ref = df['Ref_Velocity_cm_yr'].values
    insar = df['InSAR_Velocity_cm_yr'].values
    
    ax.scatter(ref, insar, s=75, alpha=0.8, edgecolor='k', linewidth=1, 
               label=label, c=color, marker=marker)
               
    # Add labels (station names) if requested
    if add_labels and 'Site' in df.columns:
        # We use arrowprops to draw a line connecting the label to the point
        for idx, row in df.iterrows():
            # Alternate label offsets to minimize overlapping
            offset_x = 25 if idx % 2 == 0 else -25
            offset_y = 20 if idx % 4 < 2 else -20
            ax.annotate(row['Site'], 
                        xy=(row['Ref_Velocity_cm_yr'], row['InSAR_Velocity_cm_yr']),
                        xytext=(offset_x, offset_y), textcoords='offset points', 
                        fontsize=10, alpha=0.9,
                        arrowprops=dict(arrowstyle="-", color='gray', lw=0.8, alpha=0.7))
               
    min_val = min(ref.min(), insar.min())
    max_val = max(ref.max(), insar.max())
    
    # Add some padding
    padding = (max_val - min_val) * 0.2
    min_val -= padding
    max_val += padding
    
    # Plot 1:1 line
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', lw=2, label='1:1 Line', zorder=0)
    
    # Calculate RMSE and R²
    rmse = np.sqrt(np.mean((insar - ref)**2))
    corr_matrix = np.corrcoef(ref, insar)
    r2 = corr_matrix[0,1]**2
    
    # Add text box with statistics
    stats_text = f'RMSE = {rmse:.2f} cm/yr\n$R^2$ = {r2:.2f}'
    props = dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray')
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=16,
            verticalalignment='top', bbox=props)
            
    # Formatting
    ax.set_xlabel(f'{label} Velocity (cm/yr)')
    ax.set_ylabel('InSAR Vertical Velocity (cm/yr)')
    ax.set_title(f'InSAR vs {label} Vertical Velocities')
    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower right', frameon=True, edgecolor='gray')
    
    # Ensure square plot area
    ax.set_aspect('equal', adjustable='box')
    
    plt.tight_layout()
    
    # Save files
    png_file = f'{out_prefix}.png'
    pdf_file = f'{out_prefix}.pdf'
    plt.savefig(png_file, dpi=300, bbox_inches='tight')
    plt.savefig(pdf_file, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved {label} plots to {png_file} and {pdf_file}")

# Load datasets
gps_df = load_and_convert('6_decompose/GPS_vert_GENERIC.csv')
leveling_df = load_and_convert('6_decompose/LEVELING_vert_GENERIC.csv')

# Generate separate plots
plot_comparison(gps_df, 'GPS', '#1f77b4', 'o', '6_decompose/InSAR_vs_GPS_Scatter', add_labels=True)
plot_comparison(leveling_df, 'Leveling', '#ff7f0e', 's', '6_decompose/InSAR_vs_Leveling_Scatter', add_labels=False)
