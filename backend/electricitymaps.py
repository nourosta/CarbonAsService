import requests

def fetch_power_breakdown(zone='FR', token='yqOVPpk1lZnhtkq1M4SK'):
    url = f"https://api.electricitymap.org/v3/power-breakdown/latest?zone={zone}"
    headers = {
        "auth-token": token
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        response = response.json()
        return response  # parsed JSON
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")