import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import numpy as np
import json

# Database connection settings
DB_NAME = 'fitness_tracker' # Replace with your db name
DB_USER = 'fitness_user' # Replace with your actual username
DB_PASSWORD = 'password'  # Replace with your actual password
DB_HOST = 'localhost' # Replace with your actual db host

# Create SQLAlchemy engine for easy read/write
engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')

# 1. Load data
print('Loading data from workouts table...')
df = pd.read_sql('SELECT * FROM workouts', engine)

# 2. Standardize activity types
activity_map = {
    'Run': 'Running', 'Running': 'Running',
    'Walk': 'Walking', 'Walking': 'Walking',
    'Ride': 'Cycling', 'Cycling': 'Cycling',
    'Swim': 'Swimming', 'Swimming': 'Swimming',
    # Add Apple Health mappings
    'HKWorkoutActivityTypeClimbing': 'Climbing',
    'HKWorkoutActivityTypeFunctionalStrengthTraining': 'Functional Strength',
    'HKWorkoutActivityTypeRunning': 'Running',
    'HKWorkoutActivityTypeTraditionalStrengthTraining': 'Traditional Strength',
    'HKWorkoutActivityTypeWalking': 'Walking',
    # Add more as needed
}
df['activity'] = df['workout_type'].map(activity_map).fillna(df['workout_type'])

# 3. Convert distance to km and duration to minutes
df['distance_km'] = df['distance'] / 1000
# Avoid division by zero for duration
with np.errstate(divide='ignore', invalid='ignore'):
    df['duration_min'] = df['duration'] / 60

# 4. Calculate pace (min/km)
df['pace_min_per_km'] = df['duration_min'] / df['distance_km']
df.loc[df['distance_km'] == 0, 'pace_min_per_km'] = None

# 5. Parse start_time as datetime and sort
df['start_time'] = pd.to_datetime(df['start_time'])
df = df.sort_values('start_time')

# 6. Calculate rolling averages and ACWR (per activity type)
df['training_load'] = df['duration_min']  # You can use distance_km or other metric

def rolling_mean(series, window):
    return series.rolling(window=window, min_periods=1).mean()

df['acute_load'] = df.groupby('activity')['training_load'].apply(lambda x: rolling_mean(x, 7)).reset_index(level=0, drop=True)
df['chronic_load'] = df.groupby('activity')['training_load'].apply(lambda x: rolling_mean(x, 28)).reset_index(level=0, drop=True)
df['acwr'] = df['acute_load'] / df['chronic_load']

# Convert raw column to JSON strings for PostgreSQL compatibility
df['raw'] = df['raw'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)

# 7. Write to new table
df.to_sql('workouts_features', engine, if_exists='replace', index=False)
print("Feature engineering complete. Data written to workouts_features table.")

# 8. (Optional) Save to CSV for quick inspection
df.to_csv('workouts_features.csv', index=False)
print("Also saved as workouts_features.csv") 