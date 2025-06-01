# Personal Fitness Dashboard

This is an interactive Streamlit application that allows you to visualize and analyze your personal fitness data from Strava. It supports uploading your `.csv` activity data, provides customizable insights, forecasts future training trends, and offers personalized tips based on your training data and age. I have provided a `.csv` file to use as an example.

## Features

- Data Upload: Import your Strava `.csv` files easily.
- Custom Insights: Select metrics like total distance, average pace, and more.
- Weekly Overview: Visualize weekly training patterns.
- Detailed Analysis: Explore acute-to-chronic workload ratio (ACWR) with risk zone insights.
- Pace & Performance: Analyze your pace distribution.
- Forecasting: Use ARIMA models to forecast future weekly distances.
- Training Tips: Get personalized advice based on your age and training data.
- Help / FAQ: Understand key concepts like ACWR, training load, and more.

## How to Use

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/personal-fitness-dashboard.git
   cd personal-fitness-dashboard

2. Install dependencies:
   ```bash
   pip install -r requirements.txt

3. Run the app:
      ```bash
      streamlit run fitness_dashboard.py

   Might have to use the following command instead:
      ```bash
      python -m streamlit run fitness_dashboard.py

4. Upload your Strava .csv file and start exploring your data!

## How to Pull Data from Strava

To load your Strava data into this app, you'll need to export it from your Strava account. Here’s how:

### 1. Set up a Strava App
- Go to [Strava API Settings](https://www.strava.com/settings/api) and create an app.
- Fill in **Application Name**, **Website**, and **Authorization Callback Domain** (use `http://localhost` for local testing).
- Copy your **Client ID** and **Client Secret** from the app settings.

### 2. Authorize Your App
- Direct your browser to the following URL (replace `YOUR_CLIENT_ID` with your Client ID and update `REDIRECT_URI` if needed):
https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all

- Log in to Strava and authorize the app.
- You will be redirected to a URL that looks like `http://localhost/?state=&code=AUTHORIZATION_CODE&scope=...`.
- Copy the **code** from the URL.

### 3. Update `extract_strava.py`
- Open `extract_strava.py` and replace the following variables with your details:

  ```python
  CLIENT_ID = 'your_client_id'
  CLIENT_SECRET = 'your_client_secret'
  CODE = 'your_authorization_code'
  REDIRECT_URI = 'http://localhost'  # or your specified callback domain
  ACCESS_TOKEN = 'your_access_token'  # leave this blank initially

- Run the script once with the exchange_code_for_token lines uncommented to exchange the code for an access token.
- Save the access token in the script under ACCESS_TOKEN.

### 4. Fetch Your Data
- Run the script:
  ```bash
  python extract_strava.py

- This will fetch your activities and save them to strava_activities.csv in the same directory.

### 5. Upload to the App
- In the app, upload your strava_activities.csv file to get started with analysis!
 
## Forecasting
This app uses ARIMA modeling to forecast your weekly distance for the next 12 weeks. The forecast can help you plan your training and avoid sudden spikes that might lead to injuries.

## Requirements
- Python 3.8+
- pandas
- numpy
- plotly
- statsmodels
- streamlit

## Notes
- Currently supports Strava data only.
- Please ensure your .csv file contains columns like distance, moving_time, start_date, and type.
- The app is designed for personal use and should not replace advice from a qualified coach or medical professional.
