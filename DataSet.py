import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_battery_data(num_rows=500):
    # Battery capacity ranges (in Ah)
    capacity_ranges = {
        "small": (30, 50),
        "medium": (60, 85),
        "large": (90, 120)
    }
    
    battery_ids = [f"Battery {i+1}" for i in range(num_rows)]
    
    # Generate realistic cycle counts (with some newer and some older batteries)
    cycle_counts = []
    for _ in range(num_rows):
        # 60% will be newer batteries, 40% older
        if random.random() < 0.6:
            cycle_counts.append(random.randint(50, 800))
        else:
            cycle_counts.append(random.randint(800, 3000))
    
    # Calculate SOH based on cycle count with some randomness
    soh_values = []
    for i in range(num_rows):
        base_soh = 100
        decay_rate = random.uniform(0.01, 0.018)  # Different batteries degrade at different rates
        
        # SOH follows a degradation curve with some randomness
        theoretical_soh = base_soh - (decay_rate * cycle_counts[i])
        # Add some random variation (±3%)
        soh = theoretical_soh + random.uniform(-3, 3)
        # Ensure SOH isn't too low or too high
        soh = max(min(soh, 100), 60)
        soh_values.append(soh)
    
    # State of Charge - random but with higher probability of being in normal ranges
    soc_values = []
    for _ in range(num_rows):
        if random.random() < 0.7:
            # Most batteries are in normal usage range
            soc_values.append(random.uniform(30, 85))
        elif random.random() < 0.5:
            # Some are nearly full
            soc_values.append(random.uniform(85, 100))
        else:
            # Some are getting low
            soc_values.append(random.uniform(10, 30))
    
    # Initial Rated Capacity - allocate different battery sizes
    initial_capacity_values = []
    for _ in range(num_rows):
        r = random.random()
        if r < 0.3:
            # Small batteries
            initial_capacity_values.append(random.uniform(*capacity_ranges["small"]))
        elif r < 0.7:
            # Medium batteries (most common)
            initial_capacity_values.append(random.uniform(*capacity_ranges["medium"]))
        else:
            # Large batteries
            initial_capacity_values.append(random.uniform(*capacity_ranges["large"]))
    
    # Calculate Full Charge Capacity based on SOH
    full_charge_capacity_values = []
    for i in range(num_rows):
        # Full charge capacity degrades with SOH
        full_charge_capacity = initial_capacity_values[i] * (soh_values[i] / 100)
        full_charge_capacity_values.append(full_charge_capacity)
    
    # Voltage ranges based on typical lithium-ion cells
    voltage_values = []
    for i in range(num_rows):
        min_v, max_v = 3.0, 4.2  # Standard lithium-ion voltage range
        
        # Voltage is primarily determined by SOC, with some noise
        base_voltage = min_v + (max_v - min_v) * (soc_values[i] / 100)
        # Add some small random variation
        voltage = base_voltage + random.uniform(-0.1, 0.1)
        voltage_values.append(max(min(voltage, max_v), min_v))
    
    # Temperature values - correlate slightly with SOC (higher SOC can lead to slightly higher temps during charging)
    temp_values = []
    for i in range(num_rows):
        base_temp = 25  # room temperature baseline
        # Higher SOC might indicate recent charging, slightly affecting temperature
        soc_effect = (soc_values[i] - 50) / 10
        
        # Add ambient temperature variation
        if random.random() < 0.7:
            # Normal operating temperature
            ambient_effect = random.uniform(-5, 5)
        else:
            # Some extreme cases
            ambient_effect = random.uniform(-10, 15)
            
        temp = base_temp + soc_effect + ambient_effect
        # Ensure temperature stays within realistic bounds
        temp = max(min(temp, 45), 10)
        temp_values.append(temp)
    
    # Internal resistance increases with age (cycle count) and correlates inversely with SOH
    resistance_values = []
    for i in range(num_rows):
        base_resistance = random.uniform(18, 25)  # Base resistance varies by battery
        growth_rate = random.uniform(0.012, 0.018)  # Different growth rates
        
        # Base resistance grows with cycles and is affected by temperature
        resistance = base_resistance + (growth_rate * cycle_counts[i])
        
        # Temperature effect (higher temp typically lowers resistance slightly)
        temp_factor = 1 - ((temp_values[i] - 25) * 0.005)
        resistance *= temp_factor
        
        # SOH effect (poorer health increases resistance)
        health_factor = 1 + ((100 - soh_values[i]) * 0.01)
        resistance *= health_factor
        
        # Add some random variation (±10%)
        resistance *= random.uniform(0.9, 1.1)
        resistance_values.append(max(resistance, 15))
    
    # Create the DataFrame
    data = {
        "Battery": battery_ids,
        "State of Charge (SOC) (%)": [round(soc, 2) for soc in soc_values],
        "State of Health (SOH) (%)": [round(soh, 2) for soh in soh_values],
        "Cycle Count": cycle_counts,
        "Initial Rated Capacity (Ah)": [round(cap, 1) for cap in initial_capacity_values],
        "Full Charge Capacity (Ah)": [round(cap, 1) for cap in full_charge_capacity_values],
        "Voltage (V)": [round(v, 3) for v in voltage_values],
        "Temperature (°C)": [round(t, 1) for t in temp_values],
        "Internal Resistance (mΩ)": [round(r, 2) for r in resistance_values],
    }
    
    return pd.DataFrame(data)

# Generate a larger dataset with 500 rows
df = generate_battery_data(500)

# Save to CSV file
file_path = 'ev_battery_health_data.csv'
df.to_csv(file_path, index=False)

# Display summary statistics and first few rows
print(df.describe())
print("\nFirst 5 rows:")
print(df.head())
print(f"\nCSV file saved to {file_path} with {len(df)} rows")