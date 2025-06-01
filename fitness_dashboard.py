import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import statsmodels.api as sm


st.set_page_config(page_title="Personal Fitness Dashboard", layout="wide")


st.title("Personal Fitness Dashboard")

# --- SESSION STATE SETUP ---
if 'step' not in st.session_state:
    st.session_state.step = 'upload'

# --- SCREEN 1: UPLOAD ---
if st.session_state.step == 'upload':
    st.header("Upload your data files")
    st.markdown("Upload your Strava CSV file to get started.")

    strava_file = st.file_uploader("Upload Strava Activities CSV", type=['csv'])

    user_age = st.number_input("Enter your age:", min_value=10, max_value=100, value=30)
    if user_age:
        st.session_state.user_age = user_age

    if strava_file:
        st.session_state.strava_df = pd.read_csv(strava_file)
        st.success("Strava data uploaded.")

    if (strava_file) and st.button("Proceed to Dashboard"):
        st.session_state.step = 'diagnostics'
        st.rerun()

# --- SCREEN 2: DIAGNOSTICS ---
elif st.session_state.step == 'diagnostics':
    # Sidebar option to select dashboard view
    dashboard_options = ['Home', 'Custom Insights', 'Weekly Overview', 'Detailed Analysis', 'Pace & Performance', 'Forecasting', 'Training Tips','Help / FAQ']
    selected_dashboard = st.sidebar.selectbox("Select Dashboard View", dashboard_options)    


    # Retrieve DataFrames from session_state
    df_strava = st.session_state.get('strava_df')
    df = pd.DataFrame()

    # Combine DataFrames
    if df_strava is not None:
        df_strava['source'] = 'strava'
        if 'duration' not in df_strava.columns: df_strava['duration'] = np.nan
        if 'totalDistance' not in df_strava.columns: df_strava['totalDistance'] = np.nan

    if df_strava is not None:
        df = pd.concat([df_strava], ignore_index=True)
    elif df_strava is not None:
        df = df_strava.copy()

    if not df.empty:
        # --- Preprocessing ---
        activity_map = {
            'Run': 'Running', 'Running': 'Running',
            'Walk': 'Walking', 'Walking': 'Walking',
            'Ride': 'Cycling', 'Cycling': 'Cycling',
            'Swim': 'Swimming', 'Swimming': 'Swimming',
        }

        if 'workoutActivityType' in df.columns and 'type' in df.columns:
            df['activity'] = df.apply(
                lambda row: activity_map.get(row['workoutActivityType'], row['workoutActivityType'])
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

        if isinstance(selected_date_range, (list, tuple)):
            if len(selected_date_range) == 1:
                start_date = end_date = selected_date_range[0]
            else:
                start_date = selected_date_range[0]
                end_date = selected_date_range[1]
        else:
            start_date = end_date = selected_date_range

        filtered_df = filtered_df[
            (filtered_df['start_time'].dt.date >= start_date) &
            (filtered_df['start_time'].dt.date <= end_date)
        ]
        
        if selected_activity != 'All':
                filtered_df = filtered_df[filtered_df['activity'] == selected_activity]

        if not filtered_df.empty:
            if selected_dashboard == 'Home':
                st.subheader("Home Dashboard")
                st.markdown("""
                Welcome to your Personal Fitness Dashboard! Here’s a quick guide to the different sections and what you’ll find in each:
                
                - **Custom Insights:**  
                Choose and view key metrics like distance, duration, pace, elevation gain, and more. Select specific metrics you care about to customize your view.

                - **Weekly Overview:**  
                See how your weekly distance and elevation gain trend over time. This helps you spot consistency and adjust your training plan accordingly.  
                (Tip: You can drag and zoom into the graphs for a closer look.)

                - **Detailed Analysis:**  
                Analyze your Acute:Chronic Workload Ratio (ACWR) to assess your training load balance. Color-coded risk zones help you manage injury risk.

                - **Pace & Performance:**  
                Visualize your pace distribution across activities. This helps you understand your performance levels and pacing strategy.

                - **Training Tips:**  
                Get personalized training tips based on your age and your Strava data. Recommendations cover progression, pace, and consistency.

                - **Help / FAQ:**  
                Find explanations for key terms like ACWR, pace, and training load. Understand what each metric means and how to use it to improve your training.

                Each dashboard is interactive, and you can filter by activity type and date range to focus on what matters most.  
                """)

                st.info("Use the sidebar to navigate to each dashboard and dive deeper into your training data.")

                st.markdown("**Note:** If you want to go back to the upload screen, click the button below.")
                if st.button("Go Back"):
                    st.session_state.step = 'upload'
                    st.rerun()


            elif selected_dashboard == 'Custom Insights':
                st.subheader("Customizable Insights")

                # Calculate metrics dynamically
                metric_options = {
                    'Total Distance (km)': filtered_df['distance'].sum() / 1000,
                    'Average Distance per Activity (km)': filtered_df['distance'].mean() / 1000,
                    'Total Moving Time (min)': filtered_df['moving_time'].sum() / 60,
                    'Average Moving Time per Activity (min)': filtered_df['moving_time'].mean() / 60,
                    'Total Elapsed Time (min)': filtered_df['elapsed_time'].sum() / 60,
                    'Average Elapsed Time per Activity (min)': filtered_df['elapsed_time'].mean() / 60,
                    'Total Elevation Gain (m)': filtered_df['total_elevation_gain'].sum(),
                    'Average Speed (m/s)': filtered_df['average_speed'].mean(),
                    'Max Speed (m/s)': filtered_df['max_speed'].max(),
                    'Total Achievements': filtered_df['achievement_count'].sum(),
                    'Total Kudos Received': filtered_df['kudos_count'].sum(),
                    'Total Comments Received': filtered_df['comment_count'].sum(),
                    'Total PRs': filtered_df['pr_count'].sum(),
                    'Total Photos': filtered_df['total_photo_count'].sum()
                }

                # Round all values
                for key in metric_options:
                    metric_options[key] = round(metric_options[key], 2)

                selected_metrics = st.multiselect(
                    "Select metrics to display:",
                    options=list(metric_options.keys()),
                    default=list(metric_options.keys())[:5]
                )

                if selected_metrics:
                    cols = st.columns(len(selected_metrics))
                    for i, metric in enumerate(selected_metrics):
                        cols[i].metric(metric, metric_options[metric])
                else:
                    st.info("Please select at least one metric to display.")

            elif selected_dashboard == 'Weekly Overview':
                # Calculate weekly metrics
                filtered_df['week'] = filtered_df['start_time'].dt.to_period('W').apply(lambda r: r.start_time)
                weekly_stats = filtered_df.groupby('week').agg({
                    'distance_km': 'sum',
                    'duration_min': 'sum',
                    'total_elevation_gain': 'sum',
                    'pace_min_per_km': 'mean',
                    'start_time': 'count'
                }).reset_index()
                weekly_stats.rename(columns={'start_time': 'activity_count'}, inplace=True)
                
                # Fig1 shows weekly distance
                st.subheader("Weekly Distance (km)")
                fig1 = px.bar(weekly_stats, x='week', y='distance_km', labels={'week': 'Week', 'distance_km': 'Distance (km)'})
                st.plotly_chart(fig1)

                
                # Plot activity count per week
                st.subheader("Number of Activities per Week")
                fig2 = px.bar(weekly_stats, x='week', y='activity_count', labels={'week': 'Week', 'activity_count': 'Activities'})
                st.plotly_chart(fig2)

                # Plot weekly elevation gain
                st.subheader("Weekly Elevation Gain (m)")
                fig3 = px.bar(weekly_stats, x='week', y='total_elevation_gain', labels={'week': 'Week', 'total_elevation_gain': 'Elevation Gain (m)'})
                st.plotly_chart(fig3)

                # Plot average pace per week
                st.subheader("Average Pace per Week (min/km)")
                fig4 = px.line(weekly_stats, x='week', y='pace_min_per_km', labels={'week': 'Week', 'pace_min_per_km': 'Avg Pace (min/km)'})
                st.plotly_chart(fig4)

                # Rolling average (4-week)
                weekly_stats['rolling_distance'] = weekly_stats['distance_km'].rolling(window=4, min_periods=1).mean()

                # Plot weekly distance with rolling average
                st.subheader("Weekly Distance with 4-Week Rolling Average (km)")
                fig5 = px.bar(weekly_stats, x='week', y='distance_km', labels={'week': 'Week', 'distance_km': 'Distance (km)'})
                fig5.add_scatter(x=weekly_stats['week'], y=weekly_stats['rolling_distance'], mode='lines', name='4-Week Avg', line=dict(color='red'))

                st.plotly_chart(fig5)

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

            elif selected_dashboard == 'Forecasting':
                st.subheader("Distance Forecasting")

                try:
                    # Calculate weekly distance
                    filtered_df['week'] = filtered_df['start_time'].dt.to_period('W').apply(lambda r: r.start_time)
                    weekly_distance = filtered_df.groupby('week')['distance_km'].sum().reset_index()

                    # Skip if there's too little data
                    if len(weekly_distance) < 10:
                        st.info("Not enough weekly data for forecasting. Please upload more activities.")
                    else:
                        # Fit ARIMA model
                        model = sm.tsa.ARIMA(weekly_distance['distance_km'], order=(1,1,1))
                        model_fit = model.fit()

                        # Forecast
                        forecast_steps = 12  # 12 weeks ahead
                        forecast = model_fit.forecast(steps=forecast_steps)
                        forecast_index = pd.date_range(start=weekly_distance['week'].max() + pd.Timedelta(weeks=1), periods=forecast_steps, freq='W')
                        forecast_df = pd.DataFrame({
                            'week': forecast_index,
                            'forecast_distance_km': forecast
                        })

                        # Plot
                        fig = px.line(weekly_distance, x='week', y='distance_km', title='Weekly Distance with ARIMA Forecast')
                        fig.add_scatter(x=forecast_df['week'], y=forecast_df['forecast_distance_km'], mode='lines+markers', name='Forecast')

                        fig.update_layout(xaxis_title='Week', yaxis_title='Distance (km)')

                        st.plotly_chart(fig)

                        # Insights
                        avg_forecast = forecast_df['forecast_distance_km'].mean()
                        st.markdown(f"**Forecast Insights:** Over the next 12 weeks, your average weekly distance is expected to be approximately **{avg_forecast:.2f} km**. Use this to plan your training accordingly!")
                except Exception as e:
                    st.warning(f"Forecasting failed: {e}")


            elif selected_dashboard == 'Training Tips':
                st.subheader("Training Tips Based on Your Strava Data")

                # Retrieve user age
                age = st.session_state.get('user_age', 30)  # fallback to 30

                # Basic Metrics
                total_distance = filtered_df['distance_km'].sum()
                avg_distance = filtered_df['distance_km'].mean()
                total_duration = filtered_df['duration_min'].sum()
                avg_pace = filtered_df['pace_min_per_km'].mean()
                num_activities = filtered_df.shape[0]
                active_days = filtered_df['start_time'].dt.date.nunique()

                # Weekly Distance Growth (if enough data)
                filtered_df['week'] = filtered_df['start_time'].dt.to_period('W').apply(lambda r: r.start_time)
                weekly_distance = filtered_df.groupby('week')['distance_km'].sum().reset_index()
                weekly_distance['distance_change'] = weekly_distance['distance_km'].pct_change() * 100

                st.markdown(f"""
                **Summary of Your Training Data:**
                - Total Distance: **{total_distance:.2f} km**
                - Average Distance per Activity: **{avg_distance:.2f} km**
                - Total Duration: **{total_duration:.2f} minutes**
                - Average Pace: **{avg_pace:.2f} min/km**
                - Number of Activities: **{num_activities}**
                - Active Days: **{active_days} days**
                """)

                st.subheader("Personalized Tips:")

                # Age-based general advice
                if age < 30:
                    st.markdown("""
                    - You're in your prime for building speed and endurance. Focus on pushing intensity and trying new training challenges.
                    - Strength training can enhance performance and reduce injury risk—consider adding it to your routine.
                    """)
                elif 30 <= age <= 50:
                    st.markdown("""
                    - Balance high-intensity workouts with adequate rest to avoid overuse injuries.
                    - Incorporate cross-training like cycling or swimming for variety and joint health.
                    - Increase your weekly mileage gradually (no more than 10% per week) to build endurance safely.
                    """)
                else:
                    st.markdown("""
                    - Consistency is key—aim for regular, steady training sessions rather than high-intensity efforts.
                    - Add mobility and strength work to maintain flexibility and prevent injuries.
                    - Prioritize recovery with sufficient rest days and consider lighter activities like walking or easy jogging.
                    """)

                # Tips based on weekly growth
                if len(weekly_distance) >= 2:
                    last_change = weekly_distance['distance_change'].iloc[-1]
                    if last_change > 10:
                        st.markdown("Your weekly distance increased by more than 10% compared to the previous week. Consider reducing the increase to avoid injury.")
                    elif last_change < -10:
                        st.markdown("Your weekly distance decreased significantly compared to the previous week. If unplanned, consider adjusting your schedule to maintain consistency.")
                    else:
                        st.markdown("Your weekly distance progression looks steady. Keep up the consistent work!")
                else:
                    st.markdown("Not enough weeks of data to analyze weekly progression. Keep logging activities to build a history.")

                # Tips based on pace
                if avg_pace < 5:
                    st.markdown("Your average pace is fast. Make sure to include easy runs to support proper recovery and reduce injury risk.")
                elif avg_pace < 7:
                    st.markdown("Your average pace is moderate. Consider adding tempo or interval workouts to improve your speed.")
                else:
                    st.markdown("Your average pace is on the slower side. Focus on building endurance and consistency before increasing speed.")

                # Tips based on consistency
                training_days_ratio = active_days / ((filtered_df['start_time'].max() - filtered_df['start_time'].min()).days + 1)
                if training_days_ratio < 0.3:
                    st.markdown("Your training days are relatively low compared to the time period analyzed. Aim for at least 3–4 sessions per week to build consistency.")
                else:
                    st.markdown("Your training consistency looks solid. Keep up the good work!")

                # General reminder
                st.markdown("Remember to schedule rest days in your plan to support adaptation and prevent overtraining.")


            elif selected_dashboard == 'Help / FAQ':
                st.subheader("Help / FAQ")

                st.markdown("""
                **Key Concepts:**

                - **ACWR (Acute: Chronic Workload Ratio)**  
                Compares your short-term training load to your long-term load. It helps you balance training intensity and avoid injury risk.

                - **Training Load**  
                Measures your activity volume, often in minutes. It helps track how much work you’re doing.

                - **Pace (min/km)**  
                The time it takes you to cover one kilometer. A lower pace means you’re faster.

                - **ACWR Risk Zones:**  
                    - **Low (<0.8):** May indicate undertraining.  
                    - **Optimal (0.8-1.3):** Balanced training.  
                    - **Caution (1.3-1.5):** Increased risk of fatigue or injury.  
                    - **High (>1.5):** High risk of injury. Reduce intensity and prioritize recovery.

                - **Weekly Overview:**  
                Shows how your training load changes weekly to spot patterns.

                - **Custom Insights:**  
                Lets you pick and compare metrics like distance, duration, and pace.

                Use this dashboard to better understand your workouts and plan your training smarter! 
                """)
        else:
            st.warning("No data matches the selected filters.")
    else:
        st.info("No data to display. Please upload files on the Upload tab.")

st.markdown("**Made by Prattyush Giriraj**")
