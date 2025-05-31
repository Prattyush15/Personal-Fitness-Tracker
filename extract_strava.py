import os
import requests
import pandas as pd

# Fill in your credentials below, do not share thes publicly
# These values should be obtained from your Strava app settings
CLIENT_ID = 'client_id_here'  # Replace with your actual Strava client ID
CLIENT_SECRET = 'client_secret_here'  # Replace with your actual Strava client secret
CODE = 'code_here'  # Replace with the authorization code you received after logging in
REDIRECT_URI = 'http://localhost'  # Replace with your redirect URI, must match the one used in Strava app settings
# After exchanging the code, you will receive an access token
ACCESS_TOKEN = 'access_token_here'  # Replace with the access token you received after exchanging the code


def exchange_code_for_token(client_id, client_secret, code, redirect_uri):
    """
    Exchange the authorization code for an access token and refresh token.
    """
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
    )
    if response.status_code != 200:
        print(f"Error exchanging code: {response.status_code} - {response.text}")
        return None
    return response.json()


def fetch_strava_activities(access_token, per_page=200, max_pages=5):
    activities = []
    for page in range(1, max_pages + 1):
        url = 'https://www.strava.com/api/v3/athlete/activities'
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {'per_page': per_page, 'page': page}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break
        page_activities = response.json()
        if not page_activities:
            break
        activities.extend(page_activities)
    return activities


def save_activities_to_csv(activities, filename='strava_activities.csv'):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    df = pd.DataFrame(activities)
    df.to_csv(file_path, index=False)
    print(f"Saved {len(df)} activities to {file_path}")


if __name__ == "__main__":
    # Uncomment the following lines to exchange code for token (first time only)
    # token_data = exchange_code_for_token(CLIENT_ID, CLIENT_SECRET, CODE, REDIRECT_URI)
    # print(token_data)
    # ACCESS_TOKEN = token_data['access_token']

    activities = fetch_strava_activities(ACCESS_TOKEN)
    save_activities_to_csv(activities) 