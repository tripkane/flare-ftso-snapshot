import json
import os
import requests
from requests.exceptions import JSONDecodeError, HTTPError

DEFAULT_GRAPHQL_URL = "https://flare-explorer.flare.network/graphql"

QUERY = """
query($first: Int!, $skip: Int!) {
  delegationChangedEvents(first: $first, skip: $skip) {
    id
    delegator
    delegatee
    amount
    blockNumber
    transactionHash
  }
}
"""


def fetch_all_delegations(url: str, first: int = 1000) -> list:
    """Fetch all delegation change events via GraphQL."""
    delegations = []
    skip = 0
    while True:
        payload = {"query": QUERY, "variables": {"first": first, "skip": skip}}
        resp = requests.post(url, json=payload, timeout=30)
        try:
            resp.raise_for_status()
        except HTTPError as exc:
            if resp.status_code == 404 and url.endswith("/graphql"):
                alt = url[:-len("graphql")] + "graphiql"
                print(f"{url} returned 404, retrying {alt}")
                url = alt
                resp = requests.post(url, json=payload, timeout=30)
                resp.raise_for_status()
            else:
                raise
        try:
            json_resp = resp.json()
        except JSONDecodeError as exc:
            snippet = resp.text[:200]
            raise RuntimeError(f"Failed to decode JSON from {url}: {snippet!r}") from exc
        data = json_resp.get("data", {}).get("delegationChangedEvents", [])
        if not data:
            break
        delegations.extend(data)
        skip += first
    return delegations


def main(network: str = "flare") -> None:
    url = os.getenv("FLARE_GRAPHQL_URL", DEFAULT_GRAPHQL_URL)
    if url.endswith("/graphiql"):
        url = url[: -len("graphiql")] + "graphql"
    print(f"Using GraphQL endpoint: {url}")
    logs = fetch_all_delegations(url)
    out_dir = os.path.join("history")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{network}_delegations.json")
    with open(path, "w") as f:
        json.dump(logs, f, indent=2)
    print(f"Saved {len(logs)} logs to {path}")


if __name__ == "__main__":
    main()
