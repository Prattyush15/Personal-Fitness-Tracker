import os
import requests
import pandas as pd

# Fill in your credentials below
CLIENT_ID = '162383'
CLIENT_SECRET = '630738fcd7c7f63ec72e13d70b97f6410c29e4ca'
CODE = '2fea5604f2851128b31da060f9a34408355aeb5a'  # Only needed for first token exchange
REDIRECT_URI = 'http://localhost'
ACCESS_TOKEN = '0d5acdb7da6cb68e68f19c436969d1411aa906b1'  # Use the new token after exchange


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