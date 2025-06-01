# Personal Fitness Dashboard

This is an interactive Streamlit application that allows you to visualize and analyze your personal fitness data from Strava. It supports uploading your `.csv` activity data, provides customizable insights, forecasts future training trends, and offers personalized tips based on your training data and age. I have provided a `.csv` file to use as an example and it can be accessed through the app by pressing the "Use Sample Data" button on the upload page!

You can now access this dashboard here: https://stravaanalysis.streamlit.app/

## Features

- Data Upload: Import your Strava `.csv` files easily.
- Custom Insights: Choose and view key training metrics like total distance, average pace, elevation gain, and more.
- Weekly Overview: Visualize your weekly distance, activity count, elevation gain, and pace trends.
- Detailed Analysis: Dive into your training load with the Acute:Chronic Workload Ratio (ACWR), risk zone highlights, rolling averages, and injury risk alerts.
- Pace & Performance: Explore your pace distribution, see pace vs. distance relationships, and track average weekly pace.
- Training Tips: Receive personalized recommendations based on your age and training trends to optimize performance and reduce injury risk.
- Help / FAQ: Find detailed explanations of key metrics like ACWR, training load, rolling averages, and more.

## How to Use

Simply use: https://stravaanalysis.streamlit.app/

## How to use locally

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/personal-fitness-dashboard.git
   cd personal-fitness-dashboard

2. Install dependencies:
   ```bash
   pip install -r requirements.txt

3. Run the app (choose one):
   ```bash
   streamlit run fitness_dashboard.py
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

## Requirements to run locally
- Python 3.8+
- pandas
- numpy
- plotly
- matplotlib
- statsmodels
- streamlit

## Notes
- Currently supports Strava data only.
- Please ensure your .csv file contains columns like distance, moving_time, start_date, and type.
- The app is designed for personal use and should not replace advice from a qualified coach or medical professional.

## Images
![image](https://github.com/user-attachments/assets/ebadac3e-cb98-43c0-b9ad-2fba66de1d47)
![image](https://github.com/user-attachments/assets/3b219b9d-c455-4831-af3f-8ee2de637ca3)
![image](https://github.com/user-attachments/assets/b8305d67-6f99-4d33-829d-97f5b82fef98)

