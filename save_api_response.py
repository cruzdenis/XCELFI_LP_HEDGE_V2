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
data = response.json()

with open('octav_api_response.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Response saved to octav_api_response.json")
print(f"Response size: {len(json.dumps(data))} bytes")
