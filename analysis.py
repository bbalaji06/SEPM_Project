import pandas as pd
import math

# Read the CSV file
file_path = 'DataSets/ev_battery_health_data.csv'
df = pd.read_csv(file_path)

# Function to calculate battery efficiency in percentage
def calculate_efficiency(row):
    soh = row['State of Health (SOH) (%)']
    soc = row['State of Charge (SOC) (%)']
    
    # Weights can be tuned based on real-world data or domain knowledge
    efficiency = (0.6 * soh + 0.4 * soc)
    
    # Optional: Clamp the value between 0 and 100
    return min(max(efficiency, 0), 100)


# Function to calculate remaining battery life span in years, months, and days
def calculate_life_span(row):
    # Estimate based on Cycle Count and SOH
    max_cycles = 2000 # Max cycles a battery can undergo in its full life
    cycle_degradation_rate = 0.5  # Battery degradation per cycle (in years)

    # Remaining life (in years) based on current cycles and SOH
    remaining_cycles = max_cycles - row['Cycle Count']
    remaining_years = remaining_cycles * cycle_degradation_rate * (row['State of Health (SOH) (%)'] / 100)

    # Convert years to months and days
    years = math.floor(remaining_years)
    remaining_months = math.floor((remaining_years - years) * 12)
    remaining_days = math.floor(((remaining_years - years) * 12 - remaining_months) * 30)

    return f"{years%15} years, {remaining_months} months, {remaining_days} days"


# Function to calculate charging and discharging rates
def calculate_charging_discharge_rate(row):
    # Charging/Discharging Rate based on Voltage, Temperature, and Internal Resistance
    if row['Voltage (V)'] > 4.0 and row['Temperature (°C)'] < 30 and row['Internal Resistance (mΩ)'] < 50:
        return 'Fast'
    elif row['Voltage (V)'] > 3.7 and row['Temperature (°C)'] < 35 and row['Internal Resistance (mΩ)'] < 75:
        return 'Moderate'
    else:
        return 'Slow'
    
# Function to calculate capacity fade
def calculate_capacity_fade(row):
    initial_capacity = row['Initial Rated Capacity (Ah)']
    full_capacity = row['Full Charge Capacity (Ah)']
    
    if initial_capacity == 0:
        return None  # avoid division by zero
    return (1 - (full_capacity / initial_capacity)) * 100


# NEW PARAMETER 1: Temperature Stress Factor (0-100)
def calculate_temperature_stress(row):
    # Optimal temperature range for lithium-ion batteries is typically 20-25°C
    # Higher or lower temperatures cause stress
    temp = row['Temperature (°C)']
    
    if 20 <= temp <= 25:
        stress = 0  # Ideal temperature range, no stress
    elif 15 <= temp < 20 or 25 < temp <= 30:
        stress = 20  # Slight stress
    elif 10 <= temp < 15 or 30 < temp <= 35:
        stress = 40  # Moderate stress
    elif 5 <= temp < 10 or 35 < temp <= 40:
        stress = 60  # High stress
    elif 0 <= temp < 5 or 40 < temp <= 45:
        stress = 80  # Very high stress
    else:
        stress = 100  # Extreme stress (below 0°C or above 45°C)
    
    return stress

# NEW PARAMETER 2: Voltage Stability Rating (1-10)
def calculate_voltage_stability(row):
    # This would ideally use voltage variance over time, but we'll simulate with available data
    voltage = row['Voltage (V)']
    soc = row['State of Charge (SOC) (%)']
    
    # Expected voltage range at different SOC levels
    # Using a simplified model - in real data you'd want historical voltage readings
    expected_voltage = 3.2 + (soc / 100) * 1.0  # Simple linear model from 3.2V (0% SOC) to 4.2V (100% SOC)
    
    # Calculate deviation from expected voltage
    deviation = abs(voltage - expected_voltage)
    
    # Convert to a 1-10 rating (10 being most stable)
    if deviation < 0.05:
        return 10
    elif deviation < 0.1:
        return 9
    elif deviation < 0.15:
        return 8
    elif deviation < 0.2:
        return 7
    elif deviation < 0.25:
        return 6
    elif deviation < 0.3:
        return 5
    elif deviation < 0.35:
        return 4
    elif deviation < 0.4:
        return 3
    elif deviation < 0.45:
        return 2
    else:
        return 1

# NEW PARAMETER 3: Battery Health Score (0-100)
def calculate_health_score(row):
    # A comprehensive score combining multiple factors
    # Weights can be adjusted based on importance
    soh_weight = 0.35
    resistance_weight = 0.25
    temp_stress_weight = 0.15
    voltage_stability_weight = 0.15
    cycle_count_weight = 0.10
    
    # Normalize cycle count (assuming max_cycles = 2000)
    max_cycles = 2000
    normalized_cycles = (1 - min(row['Cycle Count'] / max_cycles, 1)) * 100
    
    # Normalize resistance (lower is better)
    # Assuming typical range is 20-150 mΩ
    resistance = row['Internal Resistance (mΩ)']
    normalized_resistance = max(0, min(100, (150 - resistance) / 1.3))
    
    # Get temperature stress (already 0-100)
    temp_stress = row['Temperature Stress Factor']
    
    # Convert voltage stability (1-10) to 0-100
    voltage_stability = row['Voltage Stability Rating'] * 10
    
    # Calculate weighted score
    health_score = (
        soh_weight * row['State of Health (SOH) (%)'] +
        resistance_weight * normalized_resistance +
        temp_stress_weight * (100 - temp_stress) +  # Invert so lower stress is better
        voltage_stability_weight * voltage_stability +
        cycle_count_weight * normalized_cycles
    )
    
    # Round to nearest integer
    return round(health_score)

# Apply these functions to the DataFrame
df['Efficiency (%)'] = df.apply(calculate_efficiency, axis=1)
df['Life Span Remaining'] = df.apply(calculate_life_span, axis=1)
df['Charging/Discharging Rate'] = df.apply(calculate_charging_discharge_rate, axis=1)

# Apply new parameters
df['Temperature Stress Factor'] = df.apply(calculate_temperature_stress, axis=1)
df['Voltage Stability Rating'] = df.apply(calculate_voltage_stability, axis=1)
# Need to calculate Temperature Stress and Voltage Stability before Health Score
df['Battery Health Score'] = df.apply(calculate_health_score, axis=1)
df['Capacity Fade (%)'] = df.apply(calculate_capacity_fade, axis=1)

# Save the updated DataFrame to a new CSV file
df.to_csv('AnalysedData/battery_health_predictions_updated6.csv', index=False)


print("Analysis complete. The new CSV file 'battery_health_predictions_updated.csv' has been saved.")


#-----------------------------------------> Output 


print(df[["Efficiency (%)", "Charging/Discharging Rate", "Life Span Remaining", 
         "Temperature Stress Factor", "Voltage Stability Rating", "Battery Health Score",
         "Capacity Fade (%)"]])
