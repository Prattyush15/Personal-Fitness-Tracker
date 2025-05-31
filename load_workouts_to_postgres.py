import pandas as pd
import psycopg2
import json
import numpy as np

# Database connection settings
DB_NAME = 'fitness_tracker' # Replace with your db name
DB_USER = 'fitness_user' # Replace with your actual username
DB_PASSWORD = 'password'  # Replace with your actual password
DB_HOST = 'localhost' # Replace with your actual db host

def load_csv_to_db(csv_file, source):
    df = pd.read_csv(csv_file)
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
    )
    cur = conn.cursor()
    for _, row in df.iterrows():
        # Map columns for Strava and Apple Health
        workout_type = row.get('type') or row.get('workoutActivityType')
        start_time = row.get('start_date') or row.get('startDate')
        end_time = row.get('end_date') or row.get('endDate')
        duration = row.get('moving_time') or row.get('duration')
        distance = row.get('distance') or row.get('totalDistance')
        calories = row.get('calories') or row.get('totalEnergyBurned')
        # Convert NaN to None for JSON serialization
        row_dict = row.where(pd.notnull(row), None).to_dict()
        raw_json = json.dumps(row_dict)
        cur.execute(
            """
            INSERT INTO workouts (source, workout_type, start_time, end_time, duration, distance, calories, raw)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (source, workout_type, start_time, end_time, duration, distance, calories, raw_json)
        )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {len(df)} rows from {csv_file}")

if __name__ == "__main__":
    load_csv_to_db('strava_activities.csv', 'strava')
    load_csv_to_db('apple_health_workouts.csv', 'apple_health') 