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
    dashboard_options = ['Custom Insights', 'Weekly Overview', 'Detailed Analysis', 'Pace & Performance']
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

        # Additional columns
        for col in ['calories', 'elevation_gain', 'average_heartrate']:
            if col not in df.columns:
                df[col] = np.nan

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
            if selected_dashboard == 'Custom Insights':
                st.subheader("Customizable Insights")
                
                metric_options = {
                    'Total Distance (km)': filtered_df['distance_km'].sum().round(2),
                    'Total Duration (min)': filtered_df['duration_min'].sum().round(2),
                    'Average Pace (min/km)': filtered_df['pace_min_per_km'].mean().round(2),
                }

                selected_metrics = st.multiselect("Select metrics to display:", options=list(metric_options.keys()), default=list(metric_options.keys())[:3])

                cols = st.columns(len(selected_metrics))
                for i, metric in enumerate(selected_metrics):
                    cols[i].metric(metric, metric_options[metric])

            elif selected_dashboard == 'Weekly Overview':
                st.subheader("Weekly Distance (km)")
                filtered_df['week'] = filtered_df['start_time'].dt.to_period('W').apply(lambda r: r.start_time)
                weekly = filtered_df.groupby('week')['distance_km'].sum().reset_index()
                fig1 = px.bar(weekly, x='week', y='distance_km', labels={'week': 'Week', 'distance_km': 'Distance (km)'})
                st.plotly_chart(fig1)

            elif selected_dashboard == 'Detailed Analysis':
                st.subheader("Acute: Chronic Workload Ratio (ACWR)")
                filtered_df['training_load'] = filtered_df['duration_min']
                filtered_df['acute_load'] = filtered_df.groupby('activity')['training_load'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
                filtered_df['chronic_load'] = filtered_df.groupby('activity')['training_load'].transform(lambda x: x.rolling(window=28, min_periods=1).mean())

                with np.errstate(divide='ignore', invalid='ignore'):
                    filtered_df['acwr'] = filtered_df['acute_load'] / filtered_df['chronic_load']
                filtered_df['acwr'] = filtered_df['acwr'].replace([np.inf, -np.inf], np.nan)

                if 'acwr' in filtered_df.columns and not filtered_df['acwr'].dropna().empty:
                    
                    st.subheader("ACWR Risk Zones:")
                    st.markdown("""
                    - **Blue**: Low Risk (ACWR < 0.8)
                    - **Green**: Optimal Zone (0.8 <= ACWR <= 1.3)
                    - **Yellow**: Caution Zone (1.3 < ACWR <= 1.5)
                    - **Red**: High Risk (ACWR > 1.5)
                    """)

                    mean_acwr = filtered_df['acwr'].mean()
                    if mean_acwr < 0.8:
                        acwr_message = ("Your average ACWR is {:.2f}. You may be undertraining. Consider gradually increasing your training load to maintain fitness.").format(mean_acwr)
                    elif 0.8 <= mean_acwr <= 1.3:
                        acwr_message = ("Your average ACWR is {:.2f}. This is considered optimal for training adaptation and injury prevention.").format(mean_acwr)
                    elif 1.3 < mean_acwr <= 1.5:
                        acwr_message = ("Your average ACWR is {:.2f}. You are entering a slightly high risk zone. Monitor fatigue levels and plan rest days.").format(mean_acwr)
                    else:
                        acwr_message = ("Your average ACWR is {:.2f}. This is considered high risk for injury. It’s advisable to reduce workload and prioritize recovery.").format(mean_acwr)

                    st.markdown(f"""
                        <div style="font-size: 16px; color: white;">
                            <span style="font-size:24px;">ACWR Analysis:</span> {acwr_message}
                        </div>
                    """, unsafe_allow_html=True)

                    fig2 = px.line(
                        filtered_df.sort_values('start_time'),
                        x='start_time',
                        y='acwr',
                        color='activity',
                        labels={'start_time': 'Date', 'acwr': 'ACWR'},
                        line_shape='linear'
                    )

                    # Color coding ACWR risk zones
                    for i, row in filtered_df.iterrows():
                        acwr_value = row['acwr']
                        if pd.isna(acwr_value):
                            continue
                        elif acwr_value < 0.8:
                            color = 'blue'
                        elif 0.8 <= acwr_value <= 1.3:
                            color = 'green'
                        elif 1.3 < acwr_value <= 1.5:
                            color = 'yellow'
                        else:
                            color = 'red'

                        fig2.add_scatter(
                            x=[row['start_time']],
                            y=[acwr_value],
                            mode='markers',
                            marker=dict(color=color, size=8),
                            showlegend=False
                        )


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
