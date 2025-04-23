import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Read the CSV file
file_path = 'battery_health_predictions_updated.csv'
df = pd.read_csv(file_path)
def calculate_capacity_fade(row):
    initial_capacity = row['Initial Rated Capacity (Ah)']
    full_capacity = row['Full Charge Capacity (Ah)']
    if initial_capacity == 0:
        return None  # avoid division by zero
    return (1 - (full_capacity / initial_capacity)) * 100

# If your data doesn't have these fields yet, create them
if 'Efficiency (%)' not in df.columns:
    # Efficiency simulated based on SOH and Resistance
    df['Efficiency (%)'] = df['State of Health (SOH) (%)'] - (df['Internal Resistance (mΩ)'] / 10)
    df['Efficiency (%)'] = df['Efficiency (%)'].clip(60, 98)  # Keep within realistic bounds

if 'Life Span Remaining' not in df.columns:
    # Simulate remaining life based on SOH, cycle count and model
    # Synthetic life span calculation - simplified for demonstration
    max_cycles = 3000  # Assume 3000 cycles is typical battery end-of-life
    df['Remaining Cycles'] = max_cycles - df['Cycle Count']
    df['Remaining Cycles'] = df['Remaining Cycles'] * (df['State of Health (SOH) (%)'] / 85)  # Adjust by health
    
    # Convert to years (assume avg 1.2 cycles per day)
    df['Life Span Remaining'] = df['Remaining Cycles'] / (1.2 * 365)
    df['Life Span Remaining'] = df['Life Span Remaining'].clip(0, 8)  # Realistic bounds
    
    # Create nice string format (if needed for display)
    def format_years(years):
        full_years = int(years)
        months = int((years - full_years) * 12)
        days = int(((years - full_years) * 12 - months) * 30)
        return f"{full_years} years, {months} months, {days} days"
    
    df['Life Span Remaining'] = df['Life Span Remaining'].apply(format_years)

if 'Charging/Discharging Rate' not in df.columns:
    # Simulate charging rates based on battery model
    rate_options = ['Standard (1C)', 'Fast (2C)', 'Ultra-Fast (3C)']
    
    def assign_rate(model):
        if 'Pro' in model or 'Ultra' in model:
            weights = [0.2, 0.3, 0.5]  # Higher models more likely to support fast charging
        elif 'Max' in model:
            weights = [0.3, 0.5, 0.2]
        else:
            weights = [0.6, 0.3, 0.1]  # Basic models mostly standard charging
        return np.random.choice(rate_options, p=weights)
    
    if 'Battery Model' in df.columns:
        df['Charging/Discharging Rate'] = df['Battery Model'].apply(assign_rate)
    else:
        df['Charging/Discharging Rate'] = np.random.choice(rate_options, size=len(df), p=[0.5, 0.3, 0.2])

# Adding new parameters if they don't exist
if 'Temperature Stress Factor' not in df.columns:
    # Create a synthetic Temperature Stress Factor based on temperature
    temp = df['Temperature (°C)']
    
    # Apply simple logic for stress calculation
    conditions = [
        (temp >= 20) & (temp <= 25),  # Ideal range
        (temp >= 15) & (temp < 20) | (temp > 25) & (temp <= 30),
        (temp >= 10) & (temp < 15) | (temp > 30) & (temp <= 35),
        (temp >= 5) & (temp < 10) | (temp > 35) & (temp <= 40),
        (temp >= 0) & (temp < 5) | (temp > 40) & (temp <= 45)
    ]
    values = [0, 20, 40, 60, 80]
    
    df['Temperature Stress Factor'] = np.select(conditions, values, default=100)

if 'Voltage Stability Rating' not in df.columns:
    # Create a synthetic Voltage Stability Rating
    voltage = df['Voltage (V)']
    soc = df['State of Charge (SOC) (%)']
    
    # Expected voltage based on SOC (simple linear model)
    expected_voltage = 3.2 + (soc / 100) * 1.0
    
    # Calculate deviation and convert to rating
    deviation = abs(voltage - expected_voltage)
    
    conditions = [
        (deviation < 0.05),
        (deviation < 0.1),
        (deviation < 0.15),
        (deviation < 0.2),
        (deviation < 0.25),
        (deviation < 0.3),
        (deviation < 0.35),
        (deviation < 0.4),
        (deviation < 0.45)
    ]
    values = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    
    df['Voltage Stability Rating'] = np.select(conditions, values, default=1)

if 'Battery Health Score' not in df.columns:
    # Simulate Battery Health Score based on multiple factors
    soh = df['State of Health (SOH) (%)']
    resistance = df['Internal Resistance (mΩ)']
    normalized_resistance = np.maximum(0, np.minimum(100, (150 - resistance) / 1.3))
    cycle_count = df['Cycle Count']
    normalized_cycles = (1 - np.minimum(cycle_count / 2000, 1)) * 100
    
    # If we've created temperature stress and voltage stability, use them
    if 'Temperature Stress Factor' in df.columns and 'Voltage Stability Rating' in df.columns:
        temp_stress = df['Temperature Stress Factor']
        voltage_stability = df['Voltage Stability Rating'] * 10
        
        # Calculate weighted score
        df['Battery Health Score'] = round(
            0.35 * soh +
            0.25 * normalized_resistance +
            0.15 * (100 - temp_stress) +
            0.15 * voltage_stability +
            0.10 * normalized_cycles
        )
    else:
        # Simplified calculation if other factors aren't available
        df['Battery Health Score'] = round(0.6 * soh + 0.3 * normalized_resistance + 0.1 * normalized_cycles)

# Set a consistent, appealing color palette
sns.set(style="whitegrid")
custom_palette = sns.color_palette("viridis", as_cmap=True)
plt.rcParams.update({'font.size': 12})

if 'Capacity Fade (%)' not in df.columns:
    df['Capacity Fade (%)'] = df.apply(calculate_capacity_fade, axis=1)
# Set seaborn style
sns.set(style="whitegrid")
plt.rcParams.update({'font.size': 12})

# NEW VISUALIZATION: Distribution of Capacity Fade
plt.figure(figsize=(10, 6))
sns.histplot(df['Capacity Fade (%)'], bins=20, kde=True, color='coral', edgecolor='black')
plt.title('Distribution of Capacity Fade (%)', fontsize=16)
plt.xlabel('Capacity Fade (%)', fontsize=14)
plt.ylabel('Frequency', fontsize=14)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('capacity_fade_distribution.png', dpi=300, bbox_inches='tight')
plt.show()


# 1. Scatter plot with heatmap coloring - SOH vs Cycle Count
plt.figure(figsize=(12, 8))
scatter = plt.scatter(df['Cycle Count'], df['State of Health (SOH) (%)'], 
                      c=df['Internal Resistance (mΩ)'], cmap='plasma', 
                      alpha=0.7, s=80, edgecolors='w')
plt.colorbar(scatter, label='Internal Resistance (mΩ)')
plt.title('Battery Health (SOH) vs Cycle Count', fontsize=16)
plt.xlabel('Cycle Count', fontsize=14)
plt.ylabel('State of Health (%)', fontsize=14)
plt.tight_layout()
plt.savefig('battery_health_vs_cycles.png', dpi=300, bbox_inches='tight')
plt.show()


# 2. Hexbin plot - SOC vs Voltage
plt.figure(figsize=(10, 8))
hb = plt.hexbin(df['State of Charge (SOC) (%)'], df['Voltage (V)'], 
                gridsize=20, cmap='YlGnBu', mincnt=1)
cb = plt.colorbar(hb, label='Count')
plt.title('Hexbin Plot: SOC vs Voltage Distribution', fontsize=16)
plt.xlabel('State of Charge (%)', fontsize=14)
plt.ylabel('Voltage (V)', fontsize=14)
plt.tight_layout()
plt.savefig('soc_voltage_hexbin.png', dpi=300, bbox_inches='tight')
plt.show()

# 4. Kde plot - Life Span Distribution
plt.figure(figsize=(12, 6))
# Store the numeric years before formatting
if 'Life Span Remaining' not in df.columns:
    # ... existing code to calculate remaining life...
    
    # Store numeric value in a new column before formatting
    df['Life Span Years'] = df['Life Span Remaining'].copy()
    
    # Now format the Life Span Remaining column
    df['Life Span Remaining'] = df['Life Span Remaining'].apply(format_years)
else:
    # If Life Span Remaining already exists but is in string format, we need to extract numeric values
    # This regex extracts the year part from strings like "2 years, 3 months, 5 days"
    df['Life Span Years'] = df['Life Span Remaining'].str.extract(r'(\d+) years').astype(float)

# Use the numeric column for the KDE plot
sns.kdeplot(data=df, x='Life Span Years', hue='Charging/Discharging Rate',
            fill=True, common_norm=False, palette='viridis',
            alpha=0.5, linewidth=2)
plt.title('Density Plot: Remaining Life Distribution by Charging Rate', fontsize=16)
plt.xlabel('Life Span Remaining (Years)', fontsize=14)
plt.ylabel('Density', fontsize=14)
plt.tight_layout()
plt.savefig('lifespan_distribution.png', dpi=300, bbox_inches='tight')
plt.show()


# NEW VISUALIZATION: Histogram of Efficiency vs Temperature
plt.figure(figsize=(10, 6))

# Create temperature bins for grouping
temp_bins = [-20, 0, 20, 40, 60]
temp_labels = ['Below 0°C', '0-20°C', '20-40°C', 'Above 40°C']

# Group data by temperature bins and calculate mean efficiency
df['Temp Range'] = pd.cut(df['Temperature (°C)'], bins=temp_bins, labels=temp_labels)
grouped_data = df.groupby('Temp Range')['Efficiency (%)'].apply(list).to_dict()

# Create the grouped histogram
positions = range(len(temp_labels))
colors = plt.cm.viridis(np.linspace(0, 1, len(temp_labels)))

for i, (temp_range, efficiencies) in enumerate(grouped_data.items()):
    if len(efficiencies) > 0:  # Check if we have data for this range
        plt.hist(efficiencies, alpha=0.7, label=temp_range, color=colors[i], 
                 bins=15, edgecolor='black', linewidth=0.5)

plt.title('Efficiency Distribution by Temperature Range', fontsize=16)
plt.xlabel('Efficiency (%)', fontsize=14)
plt.ylabel('Frequency', fontsize=14)
plt.legend(title='Temperature Range')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('efficiency_by_temperature_histogram.png', dpi=300, bbox_inches='tight')
plt.show()

# NEW VISUALIZATION 1: Box plot for Temperature Stress Factor by Different SOH Ranges
plt.figure(figsize=(12, 7))
# Create SOH range categories
soh_bins = [0, 70, 80, 90, 100]
soh_labels = ['Critical (<70%)', 'Poor (70-80%)', 'Good (80-90%)', 'Excellent (>90%)']
df['SOH Range'] = pd.cut(df['State of Health (SOH) (%)'], bins=soh_bins, labels=soh_labels)

# Create the box plot
sns.boxplot(x='SOH Range', y='Temperature Stress Factor', data=df, palette='rocket')
plt.title('Temperature Stress Distribution by Battery Health Range', fontsize=16)
plt.xlabel('State of Health Range', fontsize=14)
plt.ylabel('Temperature Stress Factor (Lower is Better)', fontsize=14)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('temperature_stress_by_soh.png', dpi=300, bbox_inches='tight')
plt.show()



# NEW VISUALIZATION 3: Scatterplot for Battery Health Score vs Cycle Count with Temperature coloring
plt.figure(figsize=(12, 8))
scatter = plt.scatter(df['Cycle Count'], df['Battery Health Score'], 
                     c=df['Temperature (°C)'], cmap='coolwarm', 
                     alpha=0.7, s=80, edgecolors='w')
plt.colorbar(scatter, label='Temperature (°C)')
plt.title('Battery Health Score vs Cycle Count', fontsize=16)
plt.xlabel('Cycle Count', fontsize=14)
plt.ylabel('Battery Health Score (0-100)', fontsize=14)

# Add reference lines for health score ranges
plt.axhline(y=90, color='g', linestyle='--', alpha=0.7, label='Excellent (90+)')
plt.axhline(y=80, color='y', linestyle='--', alpha=0.7, label='Good (80-90)')
plt.axhline(y=70, color='orange', linestyle='--', alpha=0.7, label='Poor (70-80)')
plt.axhline(y=60, color='r', linestyle='--', alpha=0.7, label='Critical (<70)')
plt.legend(loc='lower left')

plt.tight_layout()
plt.savefig('health_score_vs_cycles.png', dpi=300, bbox_inches='tight')
plt.show()