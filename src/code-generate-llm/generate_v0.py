import os
import httpx
from openai import OpenAI

api_key_env = os.environ.get("OPENAI_API_KEY")

# Create a custom HTTP client that logs headers to see what's failing
def log_request(request):
    print(f"--> Request: {request.method} {request.url}")
    print("Headers:", dict(request.headers))

http_client = httpx.Client(event_hooks={"request": [log_request]})

client = OpenAI(
    base_url="https://ellm.nrp-nautilus.io/v1",
    api_key=api_key_env,
    http_client=http_client
)

try:
    completion = client.chat.completions.create(
        model="gpt-oss",
        messages=[
            {"role": "system", "content": "Talk like a pirate."},
            {"role": "user", "content": "How do I check if a Python object is an instance of a class?"},
        ],
    )
    print(completion.choices[0].message.content)
except Exception as e:
    print(f"\nCaught Expected Error: {e}")