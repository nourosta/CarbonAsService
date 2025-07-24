import requests

def fetch_carbon_intensity(zone='FR', token='yqOVPpk1lZnhtkq1M4SK'):
    url = f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={zone}"
    headers = {
        "auth-token": token
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data  # parsed JSON
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")
