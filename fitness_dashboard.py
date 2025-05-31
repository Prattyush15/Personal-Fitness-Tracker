import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Personal Fitness Dashboard", layout="wide")
st.title("Personal Fitness Dashboard")

# --- SESSION STATE SETUP ---
if 'step' not in st.session_state:
    st.session_state.step = 'upload'

# --- SCREEN 1: UPLOAD ---
if st.session_state.step == 'upload':
    st.header("Upload your data files")
    st.markdown("Upload your Strava and/or Apple Health CSV files to get started.")

    strava_file = st.file_uploader("Upload Strava Activities CSV", type=['csv'])
    apple_health_file = st.file_uploader("Upload Apple Health Workouts CSV", type=['csv'])

    if strava_file:
        st.session_state.strava_df = pd.read_csv(strava_file)
        st.success("Strava data uploaded.")
    if apple_health_file:
        st.session_state.apple_df = pd.read_csv(apple_health_file)
        st.success("Apple Health data uploaded.")

    if (strava_file or apple_health_file) and st.button("Proceed to Dashboard"):
        st.session_state.step = 'diagnostics'
        st.rerun()

# --- SCREEN 2: DIAGNOSTICS ---
elif st.session_state.step == 'diagnostics':
    st.header("Dashboard & Analysis")

    # Sidebar option to select dashboard view
    dashboard_options = ['Summary', 'Weekly Overview', 'Detailed Analysis', 'Pace & Performance']
    selected_dashboard = st.sidebar.selectbox("Select Dashboard View", dashboard_options)

    # Retrieve DataFrames from session_state
    df_strava = st.session_state.get('strava_df')
    df_apple_health = st.session_state.get('apple_df')
    df = pd.DataFrame()

    # Combine DataFrames
    if df_strava is not None:
        df_strava['source'] = 'strava'
        if 'duration' not in df_strava.columns: df_strava['duration'] = np.nan
        if 'totalDistance' not in df_strava.columns: df_strava['totalDistance'] = np.nan
    if df_apple_health is not None:
        df_apple_health['source'] = 'apple_health'
        if 'moving_time' not in df_apple_health.columns: df_apple_health['moving_time'] = np.nan
        if 'distance' not in df_apple_health.columns: df_apple_health['distance'] = np.nan

    if df_strava is not None and df_apple_health is not None:
        df = pd.concat([df_strava, df_apple_health], ignore_index=True)
    elif df_strava is not None:
        df = df_strava.copy()
    elif df_apple_health is not None:
        df = df_apple_health.copy()

    if not df.empty:
        # --- Preprocessing ---
        activity_map = {
            'Run': 'Running', 'Running': 'Running',
            'Walk': 'Walking', 'Walking': 'Walking',
            'Ride': 'Cycling', 'Cycling': 'Cycling',
            'Swim': 'Swimming', 'Swimming': 'Swimming',
            'HKWorkoutActivityTypeClimbing': 'Climbing',
            'HKWorkoutActivityTypeFunctionalStrengthTraining': 'Functional Strength',
            'HKWorkoutActivityTypeRunning': 'Running',
            'HKWorkoutActivityTypeTraditionalStrengthTraining': 'Traditional Strength',
            'HKWorkoutActivityTypeWalking': 'Walking',
            'HKWorkoutActivityTypeCycling': 'Cycling',
            'HKWorkoutActivityTypeSwimming': 'Swimming',
            'HKWorkoutActivityTypeOther': 'Other'
        }

        if 'workoutActivityType' in df.columns and 'type' in df.columns:
            df['activity'] = df.apply(
                lambda row: activity_map.get(row['workoutActivityType'], row['workoutActivityType'])
                if row['source'] == 'apple_health' and pd.notna(row['workoutActivityType'])
                else activity_map.get(row['type'], row['type'])
                if row['source'] == 'strava' and pd.notna(row['type'])
                else 'Unknown',
                axis=1
            )
        elif 'workoutActivityType' in df.columns:
            df['activity'] = df['workoutActivityType'].map(activity_map).fillna('Unknown')
        elif 'type' in df.columns:
            df['activity'] = df['type'].map(activity_map).fillna('Unknown')
        else:
            df['activity'] = 'Unknown'

        df['unified_duration'] = df.apply(
            lambda row: row.get('moving_time', row.get('elapsed_time')) if row['source'] == 'strava' else row.get('duration'),
            axis=1
        )
        df['unified_distance'] = df.apply(
            lambda row: row.get('distance') if row['source'] == 'strava' else row.get('totalDistance'),
            axis=1
        )

        df['duration_min'] = pd.to_numeric(df['unified_duration'], errors='coerce').fillna(0) / 60
        df['distance_km'] = pd.to_numeric(df['unified_distance'], errors='coerce').fillna(0) / 1000

        with np.errstate(divide='ignore', invalid='ignore'):
            df['pace_min_per_km'] = df['duration_min'] / df['distance_km']
        df.loc[df['distance_km'] == 0, 'pace_min_per_km'] = np.nan

        date_col = next((col for col in ['start_date', 'startDate'] if col in df.columns), None)
        if date_col:
            df['start_time'] = pd.to_datetime(df[date_col], errors='coerce', utc=True)
            df = df.dropna(subset=['start_time']).sort_values('start_time')
        else:
            st.error("Could not find a 'start_date' or 'startDate' column in your data.")
            st.stop()

        df['training_load'] = df['duration_min']
        df['acute_load'] = df.groupby('activity')['training_load'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
        df['chronic_load'] = df.groupby('activity')['training_load'].transform(lambda x: x.rolling(window=28, min_periods=1).mean())

        with np.errstate(divide='ignore', invalid='ignore'):
            df['acwr'] = df['acute_load'] / df['chronic_load']
        df['acwr'] = df['acwr'].replace([np.inf, -np.inf], np.nan)

        # --- Sidebar Filters ---
        activity_options = ['All'] + sorted(df['activity'].dropna().unique().tolist())
        selected_activity = st.sidebar.selectbox("Select Activity", activity_options)

        min_date = df['start_time'].min().date()
        max_date = df['start_time'].max().date()
        selected_date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

        filtered_df = df.copy()
        if selected_activity != 'All':
            filtered_df = filtered_df[filtered_df['activity'] == selected_activity]
        filtered_df = filtered_df[
            (filtered_df['start_time'].dt.date >= selected_date_range[0]) &
            (filtered_df['start_time'].dt.date <= selected_date_range[1])
        ]

        if not filtered_df.empty:
            # --- Different Dashboard Views ---
            if selected_dashboard == 'Summary':
                st.subheader("Summary Dashboard")
                st.metric("Total Distance (km)", filtered_df['distance_km'].sum().round(2))
                st.metric("Total Duration (min)", filtered_df['duration_min'].sum().round(2))
                st.metric("Average Pace (min/km)", filtered_df['pace_min_per_km'].mean().round(2))

            elif selected_dashboard == 'Weekly Overview':
                st.subheader("Weekly Distance (km)")
                filtered_df['week'] = filtered_df['start_time'].dt.to_period('W').apply(lambda r: r.start_time)
                weekly = filtered_df.groupby('week')['distance_km'].sum().reset_index()
                fig1 = px.bar(weekly, x='week', y='distance_km', labels={'week': 'Week', 'distance_km': 'Distance (km)'})
                st.plotly_chart(fig1)

            elif selected_dashboard == 'Detailed Analysis':
                st.subheader("Acute:Chronic Workload Ratio (ACWR)")
                if 'acwr' in filtered_df.columns and not filtered_df['acwr'].dropna().empty:
                    fig2 = px.line(filtered_df.sort_values('start_time'), x='start_time', y='acwr', color='activity', labels={'start_time': 'Date', 'acwr': 'ACWR'})
                    st.plotly_chart(fig2)
                else:
                    st.info("Not enough data to calculate ACWR.")

            elif selected_dashboard == 'Pace & Performance':
                st.subheader("Pace Distribution")
                fig3 = px.histogram(filtered_df, x='pace_min_per_km', nbins=20, labels={'pace_min_per_km': 'Pace (min/km)'})
                st.plotly_chart(fig3)

            if st.checkbox("Show Processed Data"):
                st.write(filtered_df)
        else:
            st.warning("No data matches the selected filters.")
    else:
        st.info("No data to display. Please upload files on the Upload tab.")

    if st.button("Go Back"):
        st.session_state.step = 'upload'
        st.rerun()

st.markdown("**Made by Prattyush Giriraj**")
