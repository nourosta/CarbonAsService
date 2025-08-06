import requests

def fetch_carbon_intensity(zone='FR', token='yqOVPpk1lZnhtkq1M4SK',temporal_granularity='5_minutes'):
    url = f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={zone}&temporal_granularity={temporal_granularity}"
    headers = {
        "auth-token": token
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data  # parsed JSON
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")


def fetch_history_carbon_intensity(zone='FR', token='yqOVPpk1lZnhtkq1M4SK', temporal_granularity='hourl'):
    url = f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={zone}&temporalGranularity={temporal_granularity}"
    headers = {
        "auth-token": token
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")