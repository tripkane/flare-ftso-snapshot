
import requests

def fetch_snapshot(url="https://tripkane.github.io/flare-ftso-snapshot/snapshot.json"):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    raise Exception("Failed to fetch snapshot")
