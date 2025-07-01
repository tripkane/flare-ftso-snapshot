import os
import requests

# Get your API key from environment variable
api_key = os.environ.get("FLARE_API_KEY")
if not api_key:
    raise Exception("Please provide an API key in the FLARE_API_KEY environment variable.")

# Generate the API token
token_resp = requests.post(
    "https://api.flare.io/tokens/generate",
    headers={
        "Authorization": api_key,
    },
)
token_resp.raise_for_status()
token = token_resp.json()["token"]

# Use the token to access a protected endpoint
resp = requests.get(
    "https://api.flare.io/tokens/test",
    headers={
        "Authorization": f"Bearer {token}",
    },
)
resp.raise_for_status()
print(resp.json())

GRAPHQL_URL = "https://flare-explorer.flare.network/api/v1/graphql"
REST_URL = "https://api.flare.network/ftso/providers"

# Try a simple block query (get latest block)
QUERY = """
{
  block {
    number
    hash
    timestamp
  }
}
"""

def fetch_block():
    payload = {"query": QUERY}
    try:
        response = requests.post(GRAPHQL_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            print("GraphQL errors:", data["errors"])
            return None
        return data["data"]["block"]
    except Exception as e:
        print(f"Error fetching block: {e}")
        return None

def fetch_providers():
    try:
        response = requests.get(REST_URL)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching providers: {e}")
        return []

def print_sample_block(block):
    print("\nLatest block fetched:")
    print(block)

def print_sample_providers(providers, n=5):
    print(f"\nTotal providers fetched: {len(providers)}")
    print(f"Sample {n} records:")
    for p in providers[:n]:
        print(p)

if __name__ == "__main__":
    print("Testing Flare GraphQL block fetch...")
    block = fetch_block()
    print_sample_block(block)

    print("Testing Flare REST FTSO providers fetch...")
    providers = fetch_providers()
    print_sample_providers(providers)