import os
import requests
import json

OCTAV_API_KEY = os.getenv("OCTAV_API_KEY")
WALLET_ADDRESS = "0xc1E18438Fed146D814418364134fE28cC8622B5C"

headers = {
    "Authorization": f"Bearer {OCTAV_API_KEY}",
    "Content-Type": "application/json"
}

url = "https://api.octav.fi/v1/portfolio"
params = {
    "addresses": WALLET_ADDRESS,
    "includeImages": "false",
    "waitForSync": "false"
}

response = requests.get(url, headers=headers, params=params, timeout=30)
print(f"Status Code: {response.status_code}")
print(f"Response Type: {type(response.json())}")
print(f"\nResponse JSON:")
print(json.dumps(response.json(), indent=2)[:2000])
