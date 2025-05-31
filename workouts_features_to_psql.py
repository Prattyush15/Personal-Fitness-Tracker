import pandas as pd
from sqlalchemy import create_engine

DB_NAME = 'fitness_tracker' # Replace with your db name
DB_USER = 'fitness_user' # Replace with your actual username
DB_PASSWORD = 'password'  # Replace with your actual password
DB_HOST = 'localhost' # Replace with your actual db host

engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')

df = pd.read_csv('workouts_features.csv')
df.to_sql('workouts_features', engine, if_exists='replace', index=False)
print("Loaded workouts_features.csv into workouts_features table.")
