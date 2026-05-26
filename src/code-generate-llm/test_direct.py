import os
import requests

api_key = os.environ.get("OPENAI_API_KEY")

url = "https://ellm.nrp-nautilus.io/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "curl/7.81.0"  # Pretend to be your working curl request
}

payload = {
    "model": "gpt-oss",
    "messages": [
        {"role": "system", "content": "Talk like a pirate."},
        {"role": "user", "content": "How do I check if a Python object is an instance of a class?"}
    ]
}

print("Sending direct POST request to Nautilus...")
response = requests.post(url, json=payload, headers=headers)

print(f"Status Code: {response.status_code}")
try:
    import json
    print(json.dumps(response.json(), indent=2))
except:
    print("Response Text:", response.text)