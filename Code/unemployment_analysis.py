import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Resolve paths relative to script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Set style for premium visualizations
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'figure.titlesize': 18,
    'figure.dpi': 150,
    'savefig.dpi': 300
})

# Define a professional color palette
PRIMARY_COLOR = '#1f77b4'  # Soft blue
ACCENT_COLOR = '#ff7f0e'   # Coral orange
RURAL_COLOR = '#2ca02c'    # Green
URBAN_COLOR = '#9467bd'    # Purple
DARK_GRAY = '#333333'

def create_plots_directory():
    os.makedirs(os.path.join(SCRIPT_DIR, '..', 'reports', 'figures'), exist_ok=True)
    print("Created '../reports/figures' directory.")

def load_and_clean_dataset_1(filepath):
    print(f"Loading and cleaning dataset 1: {filepath}")
    df = pd.read_csv(filepath)
    
    # Strip column names of whitespace
    df.columns = df.columns.str.strip()
    
    # Drop rows that are completely empty
    df = df.dropna(how='all')
    
    # Strip string columns
    string_cols = ['Region', 'Frequency', 'Area']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    # Clean and parse Date
    df = df.dropna(subset=['Date'])
    df['Date'] = pd.to_datetime(df['Date'].str.strip(), format='%d-%m-%Y', errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Convert numeric columns and clip to prevent division-by-zero
    num_cols = ['Estimated Unemployment Rate (%)', 'Estimated Employed', 'Estimated Labour Participation Rate (%)']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df = df.dropna(subset=num_cols)
    
    # Add demographic variables (Weighted calculations)
    u_rate_clipped = df['Estimated Unemployment Rate (%)'].clip(upper=99.9)
    lpr_clipped = df['Estimated Labour Participation Rate (%)'].clip(lower=0.1)
    
    df['Estimated Unemployed'] = df['Estimated Employed'] * (u_rate_clipped / (100.0 - u_rate_clipped))
    df['Estimated Labour Force'] = df['Estimated Employed'] + df['Estimated Unemployed']
    df['Estimated Working Age Population'] = (df['Estimated Labour Force'] / lpr_clipped) * 100.0
    
    # Add Year, Month, and period segmentations
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['MonthName'] = df['Date'].dt.strftime('%b')
    df['YearMonth'] = df['Date'].dt.to_period('M')
    
    # Define Covid Periods
    # Pre-Lockdown: May 2019 to March 2020
    # Lockdown: April 2020 to May 2020 (Strict national lockdown in India)
    # Post-Lockdown / Recovery: June 2020 onwards
    def get_period(date):
        if date < pd.Timestamp('2020-04-01'):
            return 'Pre-Lockdown'
        elif date <= pd.Timestamp('2020-05-31'):
            return 'Lockdown'
        else:
            return 'Post-Lockdown'
            
    df['Period'] = df['Date'].apply(get_period)
    
    print(f"Dataset 1 cleaned successfully. Shape: {df.shape}")
    return df

def load_and_clean_dataset_2(filepath):
    print(f"Loading and cleaning dataset 2: {filepath}")
    df = pd.read_csv(filepath)
    
    # Strip column names of whitespace
    df.columns = df.columns.str.strip()
    
    # Handle duplicate 'Region' column.
    # The 7th column represents Zone (North, South, etc.) but is named 'Region' in CSV.
    # Pandas loads it as 'Region.1' or we can check by positional index.
    cols = list(df.columns)
    for i, col in enumerate(cols):
        if col == 'Region.1' or (col == 'Region' and i == 6):
            cols[i] = 'Zone'
    df.columns = cols
    
    # Drop rows that are completely empty
    df = df.dropna(how='all')
    
    # Strip string columns
    string_cols = ['Region', 'Frequency', 'Zone']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    # Clean and parse Date
    df = df.dropna(subset=['Date'])
    df['Date'] = pd.to_datetime(df['Date'].str.strip(), format='%d-%m-%Y', errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Convert numeric columns
    num_cols = ['Estimated Unemployment Rate (%)', 'Estimated Employed', 'Estimated Labour Participation Rate (%)', 'longitude', 'latitude']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df = df.dropna(subset=['Estimated Unemployment Rate (%)', 'Estimated Employed', 'Estimated Labour Participation Rate (%)'])
    
    # Add demographic variables (Weighted calculations)
    u_rate_clipped = df['Estimated Unemployment Rate (%)'].clip(upper=99.9)
    lpr_clipped = df['Estimated Labour Participation Rate (%)'].clip(lower=0.1)
    
    df['Estimated Unemployed'] = df['Estimated Employed'] * (u_rate_clipped / (100.0 - u_rate_clipped))
    df['Estimated Labour Force'] = df['Estimated Employed'] + df['Estimated Unemployed']
    df['Estimated Working Age Population'] = (df['Estimated Labour Force'] / lpr_clipped) * 100.0
    
    # Add Year, Month, and period segmentations
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['MonthName'] = df['Date'].dt.strftime('%b')
    df['YearMonth'] = df['Date'].dt.to_period('M')
    
    # Period classification
    def get_period(date):
        if date < pd.Timestamp('2020-04-01'):
            return 'Pre-Lockdown'
        elif date <= pd.Timestamp('2020-05-31'):
            return 'Lockdown'
        else:
            return 'Post-Lockdown'
            
    df['Period'] = df['Date'].apply(get_period)
    
    print(f"Dataset 2 cleaned successfully. Shape: {df.shape}")
    return df

def calculate_weighted_metrics(group):
    total_emp = group['Estimated Employed'].sum()
    total_unemp = group['Estimated Unemployed'].sum()
    total_lf = group['Estimated Labour Force'].sum()
    total_wap = group['Estimated Working Age Population'].sum()
    
    weighted_u_rate = (total_unemp / total_lf) * 100.0 if total_lf > 0 else 0
    weighted_lpr = (total_lf / total_wap) * 100.0 if total_wap > 0 else 0
    
    return pd.Series({
        'Total Employed': total_emp,
        'Total Unemployed': total_unemp,
        'Total Labour Force': total_lf,
        'Total Working Age Population': total_wap,
        'Weighted Unemployment Rate (%)': weighted_u_rate,
        'Weighted Labour Participation Rate (%)': weighted_lpr,
        'Simple Mean Unemployment Rate (%)': group['Estimated Unemployment Rate (%)'].mean(),
        'Simple Mean LPR (%)': group['Estimated Labour Participation Rate (%)'].mean()
    })

def generate_report_statistics(df1, df2):
    print("\n--- CALCULATING SUMMARY STATISTICS ---")
    
    # 1. Rural vs Urban National Stats by Period (using df1)
    rural_urban_stats = df1.groupby(['Period', 'Area']).apply(calculate_weighted_metrics).reset_index()
    print("\nRural vs Urban Period-wise Statistics:")
    print(rural_urban_stats[['Period', 'Area', 'Weighted Unemployment Rate (%)', 'Weighted Labour Participation Rate (%)']])
    
    # 2. Overall National Stats by Period (using df1)
    national_stats = df1.groupby('Period').apply(calculate_weighted_metrics).reset_index()
    print("\nNational Period-wise Statistics (Weighted):")
    print(national_stats[['Period', 'Weighted Unemployment Rate (%)', 'Weighted Labour Participation Rate (%)', 'Total Employed']])
    
    # 3. Zone-wise Stats by Period (using df2)
    zone_stats = df2.groupby(['Period', 'Zone']).apply(calculate_weighted_metrics).reset_index()
    print("\nZone-wise Period-wise Statistics (Weighted):")
    print(zone_stats[['Period', 'Zone', 'Weighted Unemployment Rate (%)']])
    
    # 4. State-wise Lockdown Impact (using df1)
    # Calculate difference between Lockdown and Pre-Lockdown for each state
    state_period_stats = df1.groupby(['Region', 'Period']).apply(calculate_weighted_metrics).reset_index()
    state_pivot = state_period_stats.pivot(index='Region', columns='Period', values='Weighted Unemployment Rate (%)')
    state_pivot['Spike'] = state_pivot['Lockdown'] - state_pivot['Pre-Lockdown']
    state_pivot = state_pivot.sort_values(by='Spike', ascending=False)
    print("\nTop 10 States with largest Unemployment Rate spikes during lockdown:")
    print(state_pivot[['Pre-Lockdown', 'Lockdown', 'Spike']].head(10))
    
    # Save statistics tables as markdown/csv for the report
    processed_dir = os.path.join(SCRIPT_DIR, '..', 'data', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    rural_urban_stats.to_csv(os.path.join(processed_dir, 'rural_urban_period_stats.csv'), index=False)
    national_stats.to_csv(os.path.join(processed_dir, 'national_period_stats.csv'), index=False)
    zone_stats.to_csv(os.path.join(processed_dir, 'zone_period_stats.csv'), index=False)
    state_pivot.to_csv(os.path.join(processed_dir, 'state_lockdown_impact.csv'))
    print("Saved statistics tables to '../data/processed/' directory.")
    
    return rural_urban_stats, national_stats, zone_stats, state_pivot

def plot_rural_urban_trends(df1):
    print("Plotting Plot 1: Rural vs Urban Monthly Trends...")
    # Group df1 by YearMonth and Area, calculate weighted metrics
    monthly_area = df1.groupby(['YearMonth', 'Area']).apply(calculate_weighted_metrics).reset_index()
    monthly_area['DateStr'] = monthly_area['YearMonth'].dt.strftime('%b %Y')
    
    plt.figure(figsize=(12, 6.5))
    
    # Draw Rural and Urban lines
    sns.lineplot(data=monthly_area[monthly_area['Area'] == 'Rural'], 
                 x='DateStr', y='Weighted Unemployment Rate (%)', 
                 marker='o', color=RURAL_COLOR, label='Rural', linewidth=2.5, markersize=8)
    sns.lineplot(data=monthly_area[monthly_area['Area'] == 'Urban'], 
                 x='DateStr', y='Weighted Unemployment Rate (%)', 
                 marker='s', color=URBAN_COLOR, label='Urban', linewidth=2.5, markersize=8)
    
    # Add lockdown highlight
    plt.axvspan('Apr 2020', 'May 2020', color='red', alpha=0.1, label='Peak Lockdown (Apr-May 2020)')
    
    plt.title('Monthly Unemployment Rate Trends: Rural vs. Urban (May 2019 – June 2020)', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Month', fontsize=13, fontweight='bold', labelpad=10)
    plt.ylabel('Weighted Unemployment Rate (%)', fontsize=13, fontweight='bold', labelpad=10)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=11, loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(SCRIPT_DIR, '..', 'reports', 'figures', 'plot1_rural_urban_trends.png'), bbox_inches='tight')
    plt.close()

def plot_top_worst_hit_states(state_pivot):
    print("Plotting Plot 2: Top 10 Worst-Hit States...")
    top_10 = state_pivot.sort_values(by='Lockdown', ascending=False).head(10).reset_index()
    
    # Melt to long format for Seaborn grouped bar plot
    melted = pd.melt(top_10, id_vars=['Region'], value_vars=['Pre-Lockdown', 'Lockdown'],
                     var_name='Period', value_name='Unemployment Rate (%)')
    
    plt.figure(figsize=(12, 6.5))
    sns.barplot(data=melted, x='Region', y='Unemployment Rate (%)', hue='Period', 
                palette={'Pre-Lockdown': '#aec7e8', 'Lockdown': '#d62728'})
    
    plt.title('Top 10 States with Highest Unemployment Rates during Peak Lockdown', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('State / Region', fontsize=13, fontweight='bold', labelpad=10)
    plt.ylabel('Unemployment Rate (%)', fontsize=13, fontweight='bold', labelpad=10)
    plt.xticks(rotation=30, ha='right')
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Period', frameon=True, fontsize=11)
    
    # Add values on top of bars
    for p in plt.gca().patches:
        height = p.get_height()
        if height > 0:
            plt.gca().annotate(f'{height:.1f}%',
                               (p.get_x() + p.get_width() / 2., height),
                               ha='center', va='center',
                               xytext=(0, 7),
                               textcoords='offset points',
                               fontsize=9, fontweight='bold', color=DARK_GRAY)
            
    plt.tight_layout()
    plt.savefig(os.path.join(SCRIPT_DIR, '..', 'reports', 'figures', 'plot2_worst_hit_states.png'), bbox_inches='tight')
    plt.close()

def plot_rural_urban_box(df1):
    print("Plotting Plot 3: Rural vs Urban Distribution Boxplot...")
    plt.figure(figsize=(10, 6.5))
    
    sns.boxplot(data=df1, x='Area', y='Estimated Unemployment Rate (%)', hue='Period',
                palette={'Pre-Lockdown': '#aec7e8', 'Lockdown': '#ff9896', 'Post-Lockdown': '#c5b0d5'},
                linewidth=1.5, fliersize=4)
    
    plt.title('Distribution of State Unemployment Rates: Rural vs. Urban Areas', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Area Type', fontsize=13, fontweight='bold', labelpad=10)
    plt.ylabel('State-level Unemployment Rate (%)', fontsize=13, fontweight='bold', labelpad=10)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Time Period', frameon=True, fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(SCRIPT_DIR, '..', 'reports', 'figures', 'plot3_rural_urban_box.png'), bbox_inches='tight')
    plt.close()

def plot_zone_trends(df2):
    print("Plotting Plot 4: Zone-wise Trends...")
    # Group df2 by YearMonth and Zone, calculate weighted metrics
    monthly_zone = df2.groupby(['YearMonth', 'Zone']).apply(calculate_weighted_metrics).reset_index()
    monthly_zone = monthly_zone.sort_values(by='YearMonth')
    monthly_zone['DateStr'] = monthly_zone['YearMonth'].dt.strftime('%b %Y')
    
    plt.figure(figsize=(12, 6.5))
    
    # Draw a line for each zone
    zones = monthly_zone['Zone'].unique()
    markers = ['o', 's', '^', 'v', 'D', 'p']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    for i, zone in enumerate(zones):
        zone_data = monthly_zone[monthly_zone['Zone'] == zone]
        sns.lineplot(data=zone_data, x='DateStr', y='Weighted Unemployment Rate (%)', 
                     marker=markers[i % len(markers)], color=colors[i % len(colors)],
                     label=zone, linewidth=2.5, markersize=8)
        
    plt.axvspan('Apr 2020', 'May 2020', color='red', alpha=0.08, label='Peak Lockdown')
    
    plt.title('Geographic Zone Trends in Unemployment Rates (Jan 2020 – Oct 2020)', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Month', fontsize=13, fontweight='bold', labelpad=10)
    plt.ylabel('Weighted Unemployment Rate (%)', fontsize=13, fontweight='bold', labelpad=10)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title='Geographic Zone', frameon=True, facecolor='white', framealpha=0.9, fontsize=10, loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(SCRIPT_DIR, '..', 'reports', 'figures', 'plot4_zone_trends.png'), bbox_inches='tight')
    plt.close()

def plot_lfpr_vs_unemployment(df1):
    print("Plotting Plot 5: LFPR vs Unemployment...")
    # Aggregate nationally by month (df1 covers May 2019 to June 2020)
    monthly_national = df1.groupby('YearMonth').apply(calculate_weighted_metrics).reset_index()
    monthly_national['DateStr'] = monthly_national['YearMonth'].dt.strftime('%b %Y')
    
    fig, ax1 = plt.subplots(figsize=(12, 6.5))
    
    # Plot Unemployment on primary y-axis
    color = '#d62728'
    ax1.set_xlabel('Month', fontsize=13, fontweight='bold', labelpad=10)
    ax1.set_ylabel('Weighted Unemployment Rate (%)', color=color, fontsize=13, fontweight='bold', labelpad=10)
    line1 = ax1.plot(monthly_national['DateStr'], monthly_national['Weighted Unemployment Rate (%)'], 
                     color=color, marker='o', linewidth=2.5, markersize=8, label='Unemployment Rate (%)')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Plot LFPR on secondary y-axis
    ax2 = ax1.twinx()  
    color = '#1f77b4'
    ax2.set_ylabel('Weighted Labour Participation Rate (%)', color=color, fontsize=13, fontweight='bold', labelpad=10)
    line2 = ax2.plot(monthly_national['DateStr'], monthly_national['Weighted Labour Participation Rate (%)'], 
                     color=color, marker='s', linewidth=2.5, markersize=8, label='Labour Participation Rate (%)')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # Rotate x-axis labels
    ax1.set_xticklabels(monthly_national['DateStr'], rotation=45)
    
    # Highlight lockdown
    ax1.axvspan('Apr 2020', 'May 2020', color='red', alpha=0.08, label='Peak Lockdown')
    
    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', frameon=True, fontsize=11)
    
    plt.title('National Labor Market Dynamics: Unemployment vs. LFPR (May 2019 – June 2020)', fontsize=16, fontweight='bold', pad=15)
    fig.tight_layout()
    plt.savefig(os.path.join(SCRIPT_DIR, '..', 'reports', 'figures', 'plot5_lfpr_vs_unemployment.png'), bbox_inches='tight')
    plt.close()

def plot_correlation_heatmap(df1):
    print("Plotting Plot 6: Correlation Heatmap...")
    # Select key numerical columns
    cols = ['Estimated Unemployment Rate (%)', 'Estimated Employed', 
            'Estimated Labour Participation Rate (%)', 'Estimated Unemployed', 'Estimated Labour Force']
    corr = df1[cols].corr()
    
    # Rename for readability
    rename_dict = {
        'Estimated Unemployment Rate (%)': 'Unemployment Rate (%)',
        'Estimated Employed': 'Employed Population',
        'Estimated Labour Participation Rate (%)': 'LFPR (%)',
        'Estimated Unemployed': 'Unemployed Population',
        'Estimated Labour Force': 'Total Labor Force'
    }
    corr = corr.rename(index=rename_dict, columns=rename_dict)
    
    plt.figure(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr, dtype=bool)) # Mask upper triangle for cleaner look
    
    sns.heatmap(corr, mask=mask, annot=True, cmap='coolwarm', fmt=".2f",
                linewidths=0.5, square=True, cbar_kws={"shrink": .8}, annot_kws={"size": 11, "weight": "bold"})
    
    plt.title('Correlation Matrix of Indian Labor Market Indicators', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(SCRIPT_DIR, '..', 'reports', 'figures', 'plot6_correlation_heatmap.png'), bbox_inches='tight')
    plt.close()

def plot_geographic_bubble_map(df2):
    print("Plotting Plot 7: Geographic Bubble Map...")
    # Take the average coordinates and median unemployment rate during peak lockdown
    lockdown_df = df2[df2['Period'] == 'Lockdown']
    state_geo = lockdown_df.groupby('Region').agg({
        'Estimated Unemployment Rate (%)': 'mean',
        'latitude': 'first',
        'longitude': 'first',
        'Zone': 'first'
    }).reset_index()
    
    # Drop rows with missing coords
    state_geo = state_geo.dropna(subset=['latitude', 'longitude'])
    
    plt.figure(figsize=(10, 10))
    
    # We will plot states by latitude/longitude, bubble size represents unemployment rate, color represents Zone
    sns.scatterplot(
        data=state_geo, 
        x='longitude', 
        y='latitude', 
        size='Estimated Unemployment Rate (%)',
        hue='Zone',
        sizes=(100, 1500),
        alpha=0.7,
        palette='Set1',
        edgecolor='black',
        linewidth=1.2
    )
    
    # Annotate state names for top 10 highest rates
    top_states = state_geo.sort_values(by='Estimated Unemployment Rate (%)', ascending=False).head(8)
    for idx, row in top_states.iterrows():
        plt.annotate(
            row['Region'], 
            (row['longitude'], row['latitude']),
            textcoords="offset points", 
            xytext=(0,10), 
            ha='center', 
            fontsize=9, 
            fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.5)
        )
        
    plt.title('Geographical Distribution of Unemployment Rate during Peak Lockdown', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Longitude', fontsize=12, fontweight='bold')
    plt.ylabel('Latitude', fontsize=12, fontweight='bold')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(title='Zone & Unemployment Rate', loc='upper right', frameon=True, fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(SCRIPT_DIR, '..', 'reports', 'figures', 'plot7_geographic_bubble_map.png'), bbox_inches='tight')
    plt.close()

def main():
    # Filepaths
    csv1 = os.path.join(SCRIPT_DIR, '..', 'data', 'raw', 'Unemployment in India.csv')
    csv2 = os.path.join(SCRIPT_DIR, '..', 'data', 'raw', 'Unemployment_Rate_upto_11_2020.csv')
    
    # Create output directories
    create_plots_directory()
    
    # 1. Clean Data
    df1 = load_and_clean_dataset_1(csv1)
    df2 = load_and_clean_dataset_2(csv2)
    
    # 2. Run statistical calculations
    rural_urban_stats, national_stats, zone_stats, state_pivot = generate_report_statistics(df1, df2)
    
    # 3. Create visualizations
    plot_rural_urban_trends(df1)
    plot_top_worst_hit_states(state_pivot)
    plot_rural_urban_box(df1)
    plot_zone_trends(df2)
    plot_lfpr_vs_unemployment(df1)
    plot_correlation_heatmap(df1)
    plot_geographic_bubble_map(df2)
    
    print("\nSUCCESS: All calculations completed and plots generated successfully!")

if __name__ == '__main__':
    main()
